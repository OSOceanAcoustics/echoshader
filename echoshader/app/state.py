import param


class AppState(param.Parameterized):
    datasets = param.Dict(default={})
    selections = param.Dict(default={})
    values = param.Dict(default={})
