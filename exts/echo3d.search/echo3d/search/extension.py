import omni.ext
import omni.ui as ui
import omni.kit.commands
from pip_prebundle import requests


# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[echo3d.search] some_public_function was called with x: ", x)
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class Echo3dSearchExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[echo3d.search] echo3d search startup")

        self._count = 0

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                title = ui.Label("Search for models via Echo3D")
                ui.ImageWithProvider(
                    source="https://picsum.photos/200/300",
                    width=10,
                    height=10,
                )
                with ui.HStack():
                    ui.Label("Keywords:")
                    searchInput = ui.StringField()
                with ui.HStack():
                    ui.Label("API Key:")
                    apiKeyInput = ui.StringField()
                with ui.HStack():
                    ui.Label("Security Key:")
                    secKeyInput = ui.StringField()

                apiKeyInput.model.set_value("quiet-base-7038")
                secKeyInput.model.set_value("Bs4TW8MjWrYk2bTVx1SjbSwx")

                def on_click():
                    omni.kit.commands.execute('CreatePrimWithDefaultXform', prim_type='Cube',
                                              attributes={'size': 100.0,
                                                          'extent': [(-50.0, -50.0, -50.0), (50.0, 50.0, 50.0)]})

                    self._count += 1
                    searchTerm = searchInput.model.get_value_as_string()

                    api_url = "https://api.echo3d.com/search"
                    data = {
                        "key": apiKeyInput.model.get_value_as_string(),
                        "secKey": secKeyInput.model.get_value_as_string(),
                        "keywords": searchTerm,
                        "include2Dcontent": "false"
                    }

                    librarySearchRequest = requests.post(url=api_url, data=data)
                    print(librarySearchRequest.json())
                    title.text = "Showing results for: '" + searchTerm + "'"

                def on_reset():
                    self._count = 0
                    title.text = "Search for models via Echo3D"
                    searchInput.model.set_value("")

                on_reset()

                with ui.HStack():
                    ui.Button("Search", clicked_fn=on_click)
                    ui.Button("Clear", clicked_fn=on_reset)

    def on_shutdown(self):
        print("[echo3d.search] echo3d search shutdown")
