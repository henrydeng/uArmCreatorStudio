import EventsGUI   as EventsGUI
import CommandsGUI as CommandsGUI
from PyQt5        import QtCore, QtWidgets, QtGui
from Logic.Global import printf


class ControlPanel(QtWidgets.QWidget):
    """
    ControlPanel:

    Purpose: A nice clean widget that has both the EventList and CommandList displayed, and the "AddEvent" and
            "AddCommand" buttons. It is a higher level of abstraction for the purpose of handling the running of the
            robot program, instead of the nitty gritty details of the commandList and eventList.

            It"s my attempt at seperating the Logic and GUI sides of things a tiny bit. It was a failed attempt, but I
            think it"s still helpful for organization.
    """

    def __init__(self, environment, settings, parent):
        super(ControlPanel, self).__init__(parent)

        # Set up Globals
        self.env               = environment
        self.scriptTimer       = None       # Used to light up events/commands as they are run when the script is active

        # Set up GUI Globals
        self.eventList         = EventList(environment, self.refresh, parent=self)
        self.commandMenuWidget = CommandsGUI.CommandMenuWidget(parent=self)
        self.commandListStack  = QtWidgets.QStackedWidget()
        self.addEventBtn       = QtWidgets.QPushButton()
        self.deleteEventBtn    = QtWidgets.QPushButton()
        self.changeEventBtn    = QtWidgets.QPushButton()

        # Set up resources for self.refreshScript()
        self.color             = QtGui.QColor(150, 255, 150)
        self.transparent       = QtGui.QColor(QtCore.Qt.transparent)
        self.setColor          = lambda item, isColored: item.setBackground((self.transparent, self.color)[isColored])


        self.initUI()

    def initUI(self):
        # Set Up Buttons and their text
        self.addEventBtn.setText('Add Event')
        self.deleteEventBtn.setText('Delete')
        self.changeEventBtn.setText('Change')

        # Connect Button Events
        self.addEventBtn.clicked.connect(self.eventList.promptUser)
        self.deleteEventBtn.clicked.connect(self.eventList.deleteEvent)
        self.changeEventBtn.clicked.connect(self.eventList.replaceEvent)

        # Create the button horizontal layout for the 'delete' and 'change' buttons
        btnRowHLayout = QtWidgets.QHBoxLayout()
        btnRowHLayout.addWidget(self.deleteEventBtn)
        btnRowHLayout.addWidget(self.changeEventBtn)

        # Create a vertical layout for the buttons (top) and the eventList (bottom)
        eventVLayout = QtWidgets.QVBoxLayout()
        eventVLayout.addWidget(self.addEventBtn)
        eventVLayout.addLayout(btnRowHLayout)
        eventVLayout.addWidget(self.eventList)

        # Create a layout to hold the 'addCommand' button and the 'commandList'
        # Do not set a minimum size for the commandListStack. This will screw up automatic resizing for CommandList
        commandVLayout = QtWidgets.QVBoxLayout()
        commandVLayout.addWidget(self.commandListStack)
        addCmndVLayout = QtWidgets.QVBoxLayout()

        # Add the addCommand button and a placeholder commandLIst
        addCmndVLayout.addWidget(self.commandMenuWidget)

        # self.commandListStack.addWidget(CommandList(self.__shared, parent=self))

        # Put the eventLIst layout and the commandLayout next to eachother
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(eventVLayout)
        mainHLayout.addLayout(commandVLayout)
        mainHLayout.addLayout(addCmndVLayout)

        # self.setMinimumWidth(500)
        self.setLayout(mainHLayout)
        self.show()

    def refresh(self):
        '''
        Refresh which commandList is currently being displayed to the one the user has highlighted. It basically just
        goes over certain things and makes sure that everything that should be displaying, is displaying.
        '''
        # Get the currently selected event on the eventList
        selectedEvent = self.eventList.getSelectedEvent()

        # Remove all widgets on the commandList stack (not delete, though!)
        for c in range(0, self.commandListStack.count()):
            widget = self.commandListStack.widget(c)
            self.commandListStack.removeWidget(widget)


        # If user has no event selected, make a clear commandList to view
        if selectedEvent is None:
            printf('ControlPanel.refresh():ERROR: no event selected!')
            # clearList = CommandList(self.__shared, parent=self)
            # self.commandListStack.addWidget(clearList)
            # self.commandListStack.setCurrentWidget(clearList)
            return

        # Add and display the correct widget
        self.commandListStack.addWidget(selectedEvent.commandList)
        self.commandListStack.setCurrentWidget(selectedEvent.commandList)


    def setScriptModeOff(self):
        self.addEventBtn.setEnabled(True)
        self.deleteEventBtn.setEnabled(True)
        self.changeEventBtn.setEnabled(True)
        self.eventList.setLocked(False)

        if self.scriptTimer is not None:
            self.scriptTimer.stop()
            self.scriptTimer = None

            # Decolor every event
            for index in range(0, self.eventList.count()):
                eventItem = self.eventList.item(index)
                self.setColor(eventItem, False)
                commandList = self.eventList.getEventFromItem(eventItem).commandList

            # Decolor every command
            for index in range(0, commandList.count()):
                commandItem = commandList.item(index)
                self.setColor(commandItem, False)

    def setScriptModeOn(self, interpreterStatusFunction, mainWindowEndScriptFunc):
        """
        When the script is running:
            - Add/Delete/Change event buttons will be disabled
            - All CommandMenuWidget buttons will be disabled
            - CommandList will not allow deleting of widgets
            - CommandList will not allow rearranging of widgets
        """

        # Enable or disable buttons according to whether or not the script is starting or stopping
        self.addEventBtn.setEnabled(False)
        self.deleteEventBtn.setEnabled(False)
        self.changeEventBtn.setEnabled(False)
        self.eventList.setLocked(True)


        self.scriptTimer = QtCore.QTimer()
        self.scriptTimer.timeout.connect(lambda: self.refreshDrawScript(interpreterStatusFunction, mainWindowEndScriptFunc))
        self.scriptTimer.start(1000.0 / 50)  # Update at same rate as the script checks events



    def refreshDrawScript(self, getStatusFunc, mainWindowEndScriptFunc):
        currRunning = getStatusFunc()

        if currRunning is False:
            mainWindowEndScriptFunc()
            self.setScriptModeOff()
            return


        selectedItem = self.eventList.getSelectedEventItem()
        # Color any events that were active since last check, and de-color all other events


        for eventIndex in range(0, self.eventList.count()):
            eventItem = self.eventList.item(eventIndex)

            # Color transparent if the event is active, decolor if event is not active
            self.setColor(eventItem, (eventIndex in currRunning))


            # Check if the currently selected event is also one that is being run, and if that event has run any cmmnds
            if selectedItem is not eventItem:   continue



            commandList = self.eventList.getEventFromItem(eventItem).commandList
            for commandIndex in range(0, len(commandList)):
                commandItem = commandList.item(commandIndex)

                if eventIndex not in currRunning:
                    self.setColor(commandItem, False)
                else:

                    self.setColor(commandItem, (commandIndex == currRunning[eventIndex][-1]))

            #     for commandIndex in range(0, len(commandList)):
            #         commandItem = commandList.item(commandIndex)
            #         self.setColor(commandItem, False)
            # else:
            #     # Since it has run command, color the commands that have been run
            #     commandsRun = currRunning[eventIndex]
            #     for commandIndex in range(0, len(commandList)):
            #         commandItem = commandList.item(commandIndex)
            #         self.setColor(commandItem, (commandIndex in commandsRun))
            #         print(commandsRun)



    def getSaveData(self):
        return self.eventList.getSaveData()

    def loadData(self, data):
        self.eventList.loadData(data, self.env)


class EventList(QtWidgets.QListWidget):
    def __init__(self, environment, refreshControlPanel, parent):

        super(EventList, self).__init__(parent)

        # GLOBALS
        self.refreshControlPanel = refreshControlPanel
        self.env                 = environment  # Used in self.addCommand only
        self.events = {}  # A hash map of the current events in the list. The listWidget leads to the event object

        self.getEventFromItem = lambda listWidgetItem: self.events[self.itemWidget(listWidgetItem)]
        self.getEventsOrdered = lambda: [self.getEventFromItem(self.item(index)) for index in range(self.count())]

        # IMPORTANT This makes sure the ControlPanel refreshes whenever you click on an item in the list,
        # in order to display the correct commandList for the event that was clicked on.
        self.itemSelectionChanged.connect(self.refreshControlPanel)

        # The following is a function that returns a dictionary of the events, in the correct order
        # self.getEventsOrdered = lambda: [self.getEvent(self.item(index)) for index in range(self.count())]
        # self.getItemsOrdered  = lambda: [self.item(index) for index in range(self.count())]

        self.setFixedWidth(200)


    def setLocked(self, bool):
        # Used to lock the eventList and commandLists from changing anything while script is running
        events = self.getEventsOrdered()
        for event in events:
            event.commandList.setEnabled(not bool)


    def getSelectedEvent(self):
        '''
        This method returns the Event() class for the currently clicked-on event.
        This is used for displaying the correct commandList, or adding a command
        to the correct event.
        '''

        selectedItem = self.getSelectedEventItem()

        if selectedItem is None:
            printf('EventList.getSelected(): ERROR: 0 events selected')
            return None

        return self.getEventFromItem(selectedItem)

    def getSelectedEventItem(self):
        '''
        This gets the 'widget' for the currently selected event item, not the Event() object
        '''

        selectedItems = self.selectedItems()
        if len(selectedItems) == 0 or len(selectedItems) > 1:
            printf('EventList.getSelectedEventItem(): ERROR: ', len(selectedItems), ' events selected')
            return None

        if selectedItems is None:
            printf('EventList.getSelectedEventItem(): BIG ERROR: selectedEvent was none!')
            raise Exception

        selectedItem = selectedItems[0]
        return selectedItem


    def promptUser(self):
        # Open the eventPromptWindow to ask the user what event they wish to create
        objManager  = self.env.getObjectManager()
        eventPrompt = EventsGUI.EventPromptWindow(objManager, parent=self)
        if eventPrompt.accepted:
            self.addEvent(eventPrompt.chosenEvent, parameters=eventPrompt.chosenParameters)
        else:
            printf('EventList.promptUser():User rejected the prompt.')


    def addEvent(self, eventType, parameters=None, commandListSave=[]):
        '''

        :param eventType:
        :param kwargs:
            'parameters' for an event, to fill it in automatically, for loading a file
            'commandListSave' for an event, if you have commandList save to load into it, then it will generate the list
        :return: Nothing
        '''

        # If a file is loading, then optimize the process by changing it a bit.
        isLoading = len(commandListSave) > 0


        # Check if the event being added already exists in the self.events dictionary
        if not isLoading:
            for _, item in self.events.items():
                if isinstance(item, eventType) and (item.parameters == parameters or parameters is None):
                    printf('EventList.addEvent(): Event already exists, disregarding user input.')
                    return


        newEvent             = eventType(parameters)
        newCommandList       = CommandList(self.env, parent=self)

        newCommandList.loadData(commandListSave)
        newEvent.commandList =  newCommandList

        # Figure out where the event will be placed in the list by looking at the "priority" of the other events
        placeIndex = 0
        for index, event in enumerate(self.getEventsOrdered()):
            if newEvent.priority < event.priority:
                break
            placeIndex = index + 1


        # Create the widget item to visualize the event
        blankWidget = EventsGUI.EventWidget(self)
        eventWidget = newEvent.dressWidget(blankWidget)


        # Create the list item to put the widget item inside of
        listWidgetItem = QtWidgets.QListWidgetItem(self)
        listWidgetItem.setSizeHint(eventWidget.sizeHint())  # Widget will not appear without this line


        # Do some finagling so pyQt will let me insert an item at 'placeIndex' row
        self.addItem(listWidgetItem)
        lastRow = self.indexFromItem(listWidgetItem).row()
        takenlistWidgetItem = self.takeItem(lastRow)
        self.insertItem(placeIndex, takenlistWidgetItem)


        # Add the widget to the list item
        self.setItemWidget(listWidgetItem, eventWidget)


        self.events[eventWidget] = newEvent

        if not isLoading:
            self.setCurrentRow(self.count() - 1)  # Select the newly added event
            self.refreshControlPanel()  # Call for a refresh of the ControlPanel so it shows the commandList




    def deleteEvent(self):
        printf('EventList.deleteEvent(): Removing selected event')

        # Get the current item it's corresponding event
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            QtWidgets.QMessageBox.question(self, 'Error', 'You need to select an event to delete',
                                           QtWidgets.QMessageBox.Ok)
            return

        # If there are commands inside the event, ask the user if they are sure they want to delete it
        if len(self.getSelectedEvent().commandList.commands) > 0:
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                   'Are you sure you want to delete this event and all its commands?',
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.No:
                printf('EventList.addCommand(): User rejected deleting the event')
                return

        # Delete the event item and it's corresponding event
        del self.events[self.itemWidget(selectedItem)]
        self.takeItem(self.currentRow())

    def replaceEvent(self):
        # Replace one event with another, while keeping the same commandList

        printf('EventList.replaceEvent(): Changing selected event')

        # Get the current item it's corresponding event
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            QtWidgets.QMessageBox.question(self, 'Error', 'You need to select an event to change',
                                           QtWidgets.QMessageBox.Ok)
            return

        # Get the type of event you will be replacing the selected event with
        objManager  = self.env.getObjectManager()
        eventPrompt = EventsGUI.EventPromptWindow(objManager, parent=self)
        if not eventPrompt.accepted:
            printf('EventList.replaceEvent():User rejected the prompt.')
            return
        eventType = eventPrompt.chosenEvent
        params = eventPrompt.chosenParameters

        # Make sure this event does not already exist
        for e in self.events.values():
            if isinstance(e, eventType) and (e.parameters == params or params is None):
                printf('EventList.addEvent(): Event already exists, disregarding user input.')
                return

        # Actually change the event to the new type
        newEvent = eventType(params)
        newEvent.commandList = self.getEventFromItem(selectedItem).commandList  # self.events[selectedItem].commandList

        # Transfer the item widget and update the looks
        oldWidget = self.itemWidget(selectedItem)
        newEvent.dressWidget(oldWidget)

        # Update the self.events dictionary with the new event
        self.events[self.itemWidget(selectedItem)] = newEvent


    def getSaveData(self):
        '''
        Save looks like
            [
            {'typeGUI': eventType, 'typeLogic': eventLogic, 'parameters' {parameters}, 'commandList' [commandList]},
            {'typeGUI': eventType, 'typeLogic': eventLogic, 'parameters' {parameters}, 'commandList' [commandList]},
            {'typeGUI': eventType, 'typeLogic': eventLogic, 'parameters' {parameters}, 'commandList' [commandList]},
            ]

        typeLogic is a string of the class name that holds the logic for the event or command.
        '''

        eventList = []
        eventsOrdered = self.getEventsOrdered()

        for event in eventsOrdered:

            eventSave = {    'typeGUI': event.__class__.__name__,
                           'typeLogic': event.logicPair,
                          'parameters': event.parameters,
                         'commandList': event.commandList.getSaveData()}

            eventList.append(eventSave)

        return eventList

    def loadData(self, data, shared):
        self.events = {}
        self.clear()  # clear eventList

        # Fill event list with new data
        for eventSave in data:

            self.addEvent(getattr(EventsGUI, eventSave['typeGUI']),  # This converts the string 'EventClass' to an actual class
                          commandListSave =  eventSave['commandList'],
                          parameters      =  eventSave['parameters'])

        # Select the first event for viewing
        if self.count() > 0: self.setCurrentRow(0)
        self.refreshControlPanel()


class CommandList(QtWidgets.QListWidget):
    minimumWidth = 250
    maximumWidth = 1300  # This isn't actually the max width. This is the most that it will adjust for content inside it

    def __init__(self, environment, parent):  # Todo: make commandList have a parent
        super(CommandList, self).__init__()

        self.env = environment  # Should just be used in addCommand

        # GLOBALS
        self.commands = {}  # Dictionary of commands. Ex: {QListItem: MoveXYZCommand, QListItem: PickupCommand}

        # Set up the drag/drop parameters (both for dragging within the commandList, and dragging from outside
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)

        self.itemDoubleClicked.connect(self.doubleClickEvent)  # For opening the widget's window
        self.itemClicked.connect(self.clickEvent)

        # The following defines a function that returns a dictionary of the commands, in the correct order
        # self.getCommandsOrdered = lambda: [self.getCommand(self.item(index)) for index in range(self.count())]
        self.setMinimumWidth(250)

    def deleteSelected(self):
        # Delete all highlighted commands

        for item in self.selectedItems():
            del self.commands[self.itemWidget(item)]
            self.takeItem(self.row(item))

        self.refresh()  # This will update indents, which can change when you delete a command

    def refresh(self):
        # Refreshes the order and indenting of the CommandList
        zeroAndAbove = lambda i: (i < 0) * 0 + (i >= 0) * i
        indent = 0

        for index in range(self.count()):
            command = self.getCommand(self.item(index))
            commandWidget = self.itemWidget(self.item(index))

            if type(command) is CommandsGUI.StartBlockCommandGUI:
                indent += 1

            commandWidget.setIndent(zeroAndAbove(indent))
            command.indent = zeroAndAbove(indent)

            if type(command) is CommandsGUI.EndBlockCommandGUI:
                indent -= 1

        # Update the width of the commandList to the widest element within it
        # This occurs whenever items are changed, or added, to the commandList
        if self.minimumWidth < self.sizeHintForColumn(0) + 10 < self.maximumWidth:
            self.setMinimumWidth(self.sizeHintForColumn(0) + 10)


    def getCommand(self, listWidgetItem):
        # Get the Command class for the given listWidgetItem
        return self.commands[self.itemWidget(listWidgetItem)]

    def addCommand(self, commandType, parameters=None, index=None):
        '''

        :param commandType: The command that will be generated
        :param parameters: The parameters that get fed into the command (Only for loading a file)
        :param index: Place the command at a particular index, instead of the end (Only for dropping item into list)
        :return:
        '''

        # If a file is loading, then set isLoading to True. This will optimize some steps.
        isLoading = parameters is not None


        # If adding a pre-filled command (used when loading a save)
        if isLoading:
            newCommand = commandType(self.env, parameters=parameters)
        else:
            newCommand = commandType(self.env)



        # Create the widget to be placed inside the listWidgetItem
        newWidget = CommandsGUI.CommandWidget(self, self.deleteSelected)
        newWidget = newCommand.dressWidget(newWidget)     # Dress up the widget


        # Create the list widget item
        listWidgetItem = QtWidgets.QListWidgetItem(self)
        listWidgetItem.setSizeHint(newWidget.sizeHint())  # Widget will not appear without this line


        # Add list widget to commandList
        self.addItem(listWidgetItem)


        # If an index was specified, move the added widget to that index
        if index is not None:
            '''
                Because PyQt is stupid, I can't simply self.insertItem(index, listWidgetItem). I have to add it, get its
                index, 'self.takeItem' it, then 'insertItem(newIndex, listWidgetItem) it. Whatever, it works, right?
            '''
            lastRow = self.indexFromItem(listWidgetItem).row()
            takenlistWidgetItem = self.takeItem(lastRow)
            self.insertItem(index, takenlistWidgetItem)


        # Add the new command to the list of commands, linking it with its corresponding listWidgetItem
        self.setItemWidget(listWidgetItem, newWidget)
        self.commands[newWidget] = newCommand



        # Fill command with information either by opening window or loading it in. Do this after adding everything.
        if isLoading:
            newCommand.parameters = parameters
        else:
            # If this is being added by the user, then prompt the user by opening the command window.
            accepted = newCommand.openWindow()  # Get information from user
            if accepted:
                # Re-make the widget that goes on the command, so it has the new information given by the user
                newCommand.dressWidget(newWidget)     # Dress up the widget
            else:
                # If the user canceled, then delete the command
                del self.commands[newWidget]
                self.takeItem(self.row(listWidgetItem))

        # Update the width of the commandList to the widest element within it
        if not isLoading:
            self.refresh()




    # For deleting items
    def keyPressEvent(self, event):
        # Delete selected items when delete key is pressed
        if event.key() == QtCore.Qt.Key_Delete:
            self.deleteSelected()


    # For clicking and dragging Command Buttons into the list, and moving items within the list
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            super(CommandList, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super(CommandList, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # Get the mouse position, offset it by the width of the listWidgets, and get the index of that listWidget
            newPoint = event.pos()
            newPoint.setY(newPoint.y() + self.rectForIndex(self.indexFromItem(self.item(0))).height() / 2)
            dropIndex = self.indexAt(newPoint).row()
            if dropIndex == -1: dropIndex = self.count()  # If dropped at a index past the end of list, drop at end

            # Add the new dragged in widget to the index that was just found
            commandType = getattr(CommandsGUI, event.mimeData().text())
            self.addCommand(commandType, index=dropIndex)

            # For easy usability, when you drop a Test command, a StartBlock and EndBlock will drop right after it.
            if commandType is CommandsGUI.TestVariableCommandGUI or \
               commandType is CommandsGUI.ElseCommandGUI:

                self.addCommand(CommandsGUI.StartBlockCommandGUI, index=dropIndex + 1)
                self.addCommand(CommandsGUI.EndBlockCommandGUI, index=dropIndex + 2)

            event.accept()
        else:
            event.setDropAction(QtCore.Qt.MoveAction)
            super(CommandList, self).dropEvent(event)
        self.refresh()


    def doubleClickEvent(self, clickedItem):
        # Open the command window for the command that was just double clicked
        printf('CommandList.doubleClickEvent(): Opening double clicked command')

        command = self.getCommand(clickedItem)
        command.openWindow()

        # Update the current itemWidget to match the new parameters
        currentWidget = self.itemWidget(clickedItem)  # Get the current itemWidget
        command.dressWidget(currentWidget)

        self.refresh()

    def clickEvent(self, clickedItem):
        for i in range(self.count()):
            item = self.item(i)
            self.itemWidget(item).setFocused(False)

        self.itemWidget(clickedItem).setFocused(True)
        self.refresh()


    def getSaveData(self):
        commandList = []
        commandsOrdered = [self.getCommand(self.item(index)) for index in range(self.count())]

        for command in commandsOrdered:
            commandSave = {   'typeGUI': command.__class__.__name__,
                            'typeLogic': command.logicPair,
                           'parameters': command.parameters}
            commandList.append(commandSave)

        return commandList

    def loadData(self, data):
        # Clear all data on the current list
        self.commands = {}
        self.clear()

        # Fill the list with new data
        for commandSave in data:
            self.addCommand(getattr(CommandsGUI, commandSave['typeGUI']),  # Convert from string to an actual event obj
                            parameters=commandSave['parameters'])
        self.refresh()