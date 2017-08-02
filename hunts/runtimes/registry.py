# vim: set fileencoding=utf-8 :
from hunts.runtimes.iframe import IFrameRuntime
from hunts.runtimes.lua import LuaRuntime
from hunts.runtimes.regex import RegexRuntime
from hunts.runtimes.static import StaticRuntime


class RuntimesRegistry(object):
    IFRAME = 'I'
    LUA    = 'L'
    REGEX  = 'R'
    STATIC = 'S'

    RUNTIME_CHOICES = (
        (IFRAME, 'IFrame Runtime'),
        (LUA,    'Lua Runtime'),
        (REGEX,  'Regex Runtime'),
        (STATIC, 'Static Runtime'),
    )

    REGISTERED_RUNTIMES = {
        IFRAME: IFrameRuntime(),
        LUA:    LuaRuntime(),
        REGEX:  RegexRuntime(),
        STATIC: StaticRuntime(),
    }

    @staticmethod
    def evaluate(runtime, script, team_puzzle_data, user_puzzle_data, team_data, user_data):
        return RuntimesRegistry.REGISTERED_RUNTIMES[runtime].evaluate(
            script,
            team_puzzle_data=team_puzzle_data,
            user_puzzle_data=user_puzzle_data,
            team_data=team_data,
            user_data=user_data,
        )

    @staticmethod
    def validate_guess(runtime, script, guess):
        return RuntimesRegistry.REGISTERED_RUNTIMES[runtime].validate_guess(
            script,
            guess,
        )
