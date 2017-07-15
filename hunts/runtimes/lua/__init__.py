# vim: set fileencoding=utf-8 :
import os
import sys

from .. import AbstractRuntime, RuntimeExecutionError, RuntimeExecutionTimeExceededError, RuntimeMemoryExceededError, RuntimeSandboxViolationError

# TODO: Replace this with proper DLFCN support in the docker python version
orig_dlflags = sys.getdlopenflags()
sys.setdlopenflags(258)
import lupa  # noqa: E402
sys.setdlopenflags(orig_dlflags)


class LuaRuntime(AbstractRuntime):
    DEFAULT_INSTRUCTION_LIMIT = 1e6  # Instructions
    DEFAULT_MEMORY_LIMIT      = 100  # KB

    ERROR_INSTRUCTION_LIMIT_EXCEEDED = "ERROR_INSTRUCTION_LIMIT_EXCEEDED"
    ERROR_MEMORY_LIMIT_EXCEEDED      = "ERROR_MEMORY_LIMIT_EXCEEDED"
    ERROR_SANDBOX_VIOLATION          = "ERROR_SANDBOX_VIOLATION"

    def __init__(self):
        pass

    def evaluate(self, script, team_puzzle_data, user_puzzle_data, team_data, user_data):
        return_values = self._sandbox_run(script, {
            "team_puzzle_data": team_puzzle_data,
            "user_puzzle_data": user_puzzle_data,
            "team_data":        team_data,
            "user_data":        user_data,
        })

        if len(return_values) == 0:
            raise RuntimeExecutionError("Lua script did not return a value")

        return return_values[0]

    def validate_guess(self, validator, guess, team_puzzle_data, team_data):
        return_values = self._sandbox_run(validator, {
            "guess":            guess,
            "team_puzzle_data": team_puzzle_data,
            "team_data":        team_data,
        })

        if len(return_values) == 0:
            raise RuntimeExecutionError("Lua script did not return a value")

        return return_values[0]

    def _create_lua_runtime(self):
        # noinspection PyArgumentList
        lua = lupa.LuaRuntime(
            register_eval=False,
            register_builtins=False,
            unpack_returned_tuples=True,
        )

        # Ensure the local is consistent and ignore system Lua paths
        lua.execute("assert(os.setlocale('C'))")
        lua.globals().package.path  = ';'.join([
            os.path.join(os.path.dirname(__file__), "?.lua"),
            "/opt/hunter2/share/lua/5.2/?.lua",
        ])

        # TODO: Support cross platform libraries
        lua.globals().package.cpath = ';'.join([
            "/opt/hunter2/lib/lua/5.2/?.so",
        ])

        return lua

    def _sandbox_run(
            self,
            lua_script,
            parameters=None,
            instruction_limit=DEFAULT_INSTRUCTION_LIMIT,
            memory_limit=DEFAULT_MEMORY_LIMIT):
        lua = self._create_lua_runtime()

        # Load the sandbox Lua module
        sandbox = lua.require('sandbox')

        # Load parameters into the sandbox
        if parameters is not None:
            for key, value in parameters.items():
                if sandbox.env[key] is not None:
                    raise RuntimeExecutionError("Passed parameter '{}' overrides sandbox environment".format(key))
                else:
                    sandbox.env[key] = value

        # Enable instruction and memory limits
        sandbox.enable_limits(instruction_limit, memory_limit)

        # The 'result' object here can be either a bool or a tuple depending on
        # the result of the Lua function, the following results are possible:
        #  - True:           script succeeded but returned nothing
        #  - (True, ...):    script succeeded with return values
        #  - (False, error): script raised an error during execution
        #  - (None, error):  script syntax loading error
        try:
            result = sandbox.run(lua_script)
            # If just a bool, return the empty result for success
            if isinstance(result, bool) and result is True:
                return []

            # Check result of executing the Lua script
            if result[0] is not True:
                exit_status, error = result

                if exit_status is None:
                    raise SyntaxError(error)

                if exit_status is False:
                    if str(error).endswith(self.ERROR_INSTRUCTION_LIMIT_EXCEEDED):
                        raise RuntimeExecutionTimeExceededError()
                    elif str(error).endswith(self.ERROR_MEMORY_LIMIT_EXCEEDED):
                        raise RuntimeMemoryExceededError()
                    elif str(error).endswith(self.ERROR_SANDBOX_VIOLATION):
                        raise RuntimeSandboxViolationError(str(error).replace(" " + self.ERROR_SANDBOX_VIOLATION, ""))
                    else:
                        raise RuntimeExecutionError(error)
            else:
                # Expand the return values to a list and return
                exit_status, *return_values = result
                return return_values

        except lupa.LuaError as error:
            # An error has occurred in the sandbox runtime itself
            raise RuntimeExecutionError("Sandbox") from error
