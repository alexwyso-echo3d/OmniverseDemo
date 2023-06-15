import omni.ext
import omni.ui as ui
import omni.kit.commands
from pip_prebundle import requests


# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[echo3d.search] some_public_function was called with x: ", x)
    return x ** x


# Constants
IMAGES_PER_PAGE = 7

# Global variables
current_search_page = 0
current_project_page = 0

# Create image widgets for displaying images
search_image_widgets = [ui.Image() for _ in range(IMAGES_PER_PAGE)]
project_image_widgets = [ui.Image() for _ in range(IMAGES_PER_PAGE)]

searchJsonData = []
projectJsonData = []


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class Echo3dSearchExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[echo3D] echo3D startup")

        # Define functions for search feature
        def update_search_images():
            start_index = current_search_page * IMAGES_PER_PAGE
            end_index = start_index + IMAGES_PER_PAGE
            for i in range(start_index, end_index):
                if i < len(searchJsonData):
                    search_image_widgets[i % IMAGES_PER_PAGE].source_url = searchJsonData[i]["thumbnail"]
                else:
                    search_image_widgets[i % IMAGES_PER_PAGE].source_url = ""

        def on_click_left_arrow_search():
            global current_search_page
            current_search_page -= 1
            global searchJsonData
            update_search_images(searchJsonData)

        def on_click_right_arrow_search():
            global current_search_page
            current_search_page += 1
            global searchJsonData
            update_search_images(searchJsonData)

        def on_click_search():
            searchTerm = searchInput.model.get_value_as_string()

            api_url = "https://api.echo3d.com/search"
            data = {
                "key": apiKeyInput.model.get_value_as_string(),
                "secKey": secKeyInput.model.get_value_as_string(),
                "keywords": searchTerm,
                "include2Dcontent": "false"
            }

            librarySearchRequest = requests.post(url=api_url, data=data)
            global searchJsonData
            searchJsonData = librarySearchRequest.json()
            searchLabel.text = "Showing results for: '" + searchTerm + "'"
            global search_image_widgets
            for i in range(IMAGES_PER_PAGE):
                if i < len(searchJsonData):
                    search_image_widgets[i].source_url = librarySearchRequest.json()[i]["thumbnail"]
                else:
                    search_image_widgets[i].source_url = ""
  
        def on_reset_search():
            searchLabel.text = "Keywords:"
            searchInput.model.set_value("")
            global search_image_widgets
            for i in range(IMAGES_PER_PAGE):
                search_image_widgets[i].source_url = ""

        # Define functions for project querying
        def update_project_images():
            start_index = current_project_page * IMAGES_PER_PAGE
            end_index = start_index + IMAGES_PER_PAGE
            for i in range(start_index, end_index):
                if i < len(projectJsonData):
                    baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
                    imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
                    project_image_widgets[i % IMAGES_PER_PAGE].source_url = baseUrl + imageFilename
                else:
                    project_image_widgets[i % IMAGES_PER_PAGE].source_url = ""

        def on_click_left_arrow_project():
            global current_project_page
            current_project_page -= 1
            global projectJsonData
            update_project_images(projectJsonData)

        def on_click_right_arrow_project():
            global current_project_page
            current_project_page += 1
            global projectJsonData
            update_project_images(projectJsonData)

        def on_click_load_project():
            api_url = "https://api.echo3d.com/query"
            data = {
                "key": apiKeyInput.model.get_value_as_string(),
                "secKey": secKeyInput.model.get_value_as_string(),
            }

            projectQueryRequest = requests.post(url=api_url, data=data).json()["db"]
            values = list(projectQueryRequest.values())

            global projectJsonData
            projectJsonData = values
            global project_image_widgets
            for i in range(IMAGES_PER_PAGE):
                if i < len(projectJsonData):
                    baseUrl = 'https://storage.echo3d.co/' + apiKeyInput.model.get_value_as_string() + "/"
                    imageFilename = projectJsonData[i]["additionalData"]["screenshotStorageID"]
                    project_image_widgets[i].source_url = baseUrl + imageFilename
                else:
                    project_image_widgets[i].source_url = ""

        # Display the UI
        self._window = ui.Window("Echo3D", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                with ui.HStack():
                    ui.Label("Connect to your Echo3D Project:")
                    ui.Label("API Key:")
                    apiKeyInput = ui.StringField()
                    ui.Label("Security Key:")
                    secKeyInput = ui.StringField()
                    ui.Button("Load Project", clicked_fn=on_click_load_project)

                apiKeyInput.model.set_value("summer-darkness-5935")
                secKeyInput.model.set_value("T8tbDSXApoJ1dQLnG0b3qPyY")

                global project_image_widgets
                with ui.HStack():
                    ui.Button("<", clicked_fn=on_click_left_arrow_project)
                    for i in range(IMAGES_PER_PAGE):
                        project_image_widgets[i] = ui.Image("")
                    ui.Button(">", clicked_fn=on_click_right_arrow_project)

                with ui.HStack():
                    searchLabel = ui.Label("Keywords:")
                    searchInput = ui.StringField()
                    with ui.VStack():
                        ui.Button("Search", clicked_fn=on_click_search)
                        ui.Button("Clear", clicked_fn=on_reset_search)

                on_reset_search()

                global search_image_widgets
                with ui.HStack():
                    ui.Button("<", clicked_fn=on_click_left_arrow_search)
                    for i in range(IMAGES_PER_PAGE):
                        search_image_widgets[i] = ui.Image("")
                    ui.Button(">", clicked_fn=on_click_right_arrow_search)

    def on_shutdown(self):
        print("[echo3D] echo3D shutdown")
