""" Main Module """

import json
import logging
import os
import subprocess
import glob

# pylint: disable=import-error
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

LOGGING = logging.getLogger(__name__)

def readWorkspaces():
    absPath = os.path.expanduser('~/.config/Code/User/workspaceStorage/')
    fileList = glob.glob(absPath + "*/workspace.json")
    dirList = []
    for workspacePath in fileList:
        f = open(workspacePath, 'r')
        data = json.load(f)
        f.close()
        pointer = data['folder'].find('file://')
        if(pointer >= 0):
            path = data['folder'][7:]
            # get workspace name
            namePointer = path.rfind('/')
            name = path[namePointer + 1:]
            currentData = {
                'name' : name,
                'path' : path
            }
            dirList.append(currentData)
    return dirList

class VSCodeProjectsExtension(Extension):
    """ Main Extension Class  """

    def __init__(self):
        """ Initializes the extension """
        super(VSCodeProjectsExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    """ Listener that handles the user input """

    # pylint: disable=unused-argument,no-self-use
    def on_event(self, event, extension):
        """ Handles the event """
        items = []

        full_project_path = os.path.expanduser(extension.preferences['projects_file_path'])
        query = event.get_argument()
        if not os.path.exists(full_project_path):
            workspaceDir = readWorkspaces()
            if query:
                workspaceDir = [
                    x for x in workspaceDir
                    if query.strip().lower() in x['name'].lower()
                ]
            if len(workspaceDir) > 0:
                for item in workspaceDir[:8]:
                    items.append(
                    ExtensionResultItem(icon='images/icon.png',
                                        name=item['name'],
                                        description=item['path'],
                                        on_enter=ExtensionCustomAction(item),
                                        on_alt_enter=OpenAction(item['path'])))

                return RenderResultListAction(items)
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Projects file not found',
                    description='Please make sure you have the Project Manager VSCode extension properly installed',  # pylint: disable=line-too-long
                    on_enter=HideWindowAction())
            ])

        if os.path.isfile(full_project_path):
            with open(full_project_path) as projects_file:
                projects = json.load(projects_file)
        else:
            project_files = os.listdir(full_project_path)
            projects = []
            for projects_file in project_files:
                projects_file = os.path.join(full_project_path, projects_file)
                with open(projects_file) as file:
                    projects += json.load(file)

        if query:
            projects = [
                x for x in projects
                if query.strip().lower() in x['name'].lower()
            ]

        for project in projects[:8]:
            items.append(
                ExtensionResultItem(icon='images/icon.png',
                                    name=project['name'],
                                    description=project.get('fullPath') or project.get('rootPath'),
                                    on_enter=ExtensionCustomAction(project),
                                    on_alt_enter=OpenAction(
                                        project.get('fullPath') or project.get('rootPath'))))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    """ Handles item enter """

    def on_event(self, event, extension):
        """ Event handler """
        data = event.get_data()

        code_executable = extension.preferences['code_executable_path']
        subprocess.call([code_executable, data.get('fullPath') or data.get('rootPath') or data.get("path")])


if __name__ == '__main__':
    VSCodeProjectsExtension().run()
    