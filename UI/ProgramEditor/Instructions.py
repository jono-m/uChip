from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QScrollArea
from PySide6.QtCore import Qt

instructions = """
<u><b>Built-ins</b></u>

    <i>Parameter(name: str)</i>
            Returns the current value of the parameter with the name <i>name</i>.
    <i>Valve(name: str)</i>
            Returns the <i>Valve</i> object for the valve name <i>name</i>.
    <i>Program(programName: str, parameters: Dict[str, Any])</i>
            Returns a new <i>Program instance</i> object to run the program named <i>programName</i> with parameters <i>parameters</i>.
            <i>parameters</i> is a dictionary mapping from the parameter name to its value. 
    <i>Preset(name: str)</i>
            Returns the <i>Program instance</i> for the program preset named <i>name</i>.
    <i>SetValve(valve: Valve object, state: [OPEN, CLOSED])</i>
            Sets the state of valve <i>valve</i> to <i>state</i>.
    <i>GetValve(valve: Valve object)</i>
            Returns the current state (OPEN or CLOSED) for valve <i>valve</i>.
    <i>Start(instance: Program instance)</i>
            Starts the program instance <i>instance</i>.
    <i>IsRunning(instance: Program instance object)</i>
            Checks if the program instance <i>instance</i> is running.
    <i>Stop(instance: Program instance object)</i>
            Stops execution of the program instance <i>instance</i>.
    <i>Pause(instance: Program instance object)</i>
            Pauses the program instance <i>instance</i>.
    <i>IsPaused(instance: Program instance object)</i>
            Checks if the program instance <i>instance</i> is paused.
    <i>Resume(instance: Program instance object)</i>
            Resumes the program instance <i>instance</i>.
    <i>print(text: str)</i>
            Prints <i>text</i> to the uChip console.
    <i>WaitForSeconds(seconds: float)</i>
            To be used in a <i>yield</i> statement. Will pause execution for <i>seconds</i> seconds.
    <i>OPEN</i>
            Valve state macro for an open valve 
    <i>CLOSED</i>
            Valve state macro for a closed valve

<u><b>Program Control</b></u>

    Use <i>yield</i> to pause program execution. This can be used to wait for a certain amount of time, until a different program is finished, or until the next program tick (to allow other programs to run concurrently).
    <i>yield WaitForSeconds(seconds: float)</i> will pause the program for <i>seconds</i> seconds.
    <i>yield [PROGRAM INSTANCE]</i> will pause the program until the given program instance is finished.
    <i>yield</i> will pause the program for one tick, to let other programs update.  
"""[1:].replace("\n", "<br>").replace(" ", "&nbsp;")


class Instructions(QFrame):
    def __init__(self):
        super().__init__()

        instructionsArea = QScrollArea()
        instructionsLabel = QLabel(instructions)
        instructionsArea.setWidget(instructionsLabel)
        instructionsArea.setWidgetResizable(True)
        instructionsArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        instructionsArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.layout().addWidget(instructionsArea)
