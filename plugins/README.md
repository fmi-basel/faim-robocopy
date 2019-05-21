# FAIM-Robocopy plugins

FAIM-Robocopy supports adding your own plugins. Plugins are detected
by the following file name pattern:

```
plugins/<plugin_folder_name>/plugin.py
```

**NOTE** Only install plugins from trusted sources!

## Exemplar

The following plugin exemplar could be placed in ```plugins/helloworld/plugins.py```:

```
class HelloWorldPlugin:
    '''
    '''

    # Description used in GUI.
    description = 'Hello world'

    # Optional: Tooltip message in GUI.
    tooltip = 'This plugin will do stuff and things'

    def __init__(self, shared_resources):
        '''shared_resources can be used to access the current parameters of FAIM-Robocopy such as source and destination folders.
        '''
        self.shared_resources = shared_resources
        ...

    def on_activation(self):
        '''will be called on activation of the plugin.
        '''
        ...

    def on_call(self):
        '''Optional. Can be called from the GUI at any point.
        '''
        ...

    def on_task_end(self):
        '''will be called at the end of a robocopy task.
        '''
        ...
```


