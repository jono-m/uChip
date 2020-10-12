stylesheet = """
        #Container {
            border-width: 0px;
        }
        *, QTabBar {
            background-color: rgba(50, 50, 50, 1);
            border-color: rgba(80, 80, 80, 1);
            color: rgba(230, 230, 230, 1);
            border-style: solid;
            border-width: 0px;
       } 
       MenuBar {
            border-width: 0px 0px 1px 0px;
       }
       #MainToolbar {
            border-width: 0px 0px 1px 0px;
       }
        QScrollArea {
            background-color: rgba(0, 0, 0, 0.2);
        }
        QScrollBar {
            background-color: rgba(255, 255, 255, 0);
            width: 10px;
        }
        QScrollBar:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        QScrollBar::handle {
            background-color: rgba(255, 255, 255, 0.2);
        }
        QScrollBar::handle:hover {
            background-color: rgba(255, 255, 255, 0.4);
        }
        QScrollBar::add-page, QScrollBar::sub-page {
            background: none;
        }
        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }
        QScrollBar::up-arrow, QScrollBar::down-arrow {
            border: none;
            background: none;
            color: none;
            width: 0;
            height: 0;
        }
        QMenuBar::item:selected, QMenu::item:selected {
            background-color: rgba(0, 0, 0, 0.3);
            color: white;
        }
        QPushButton, QToolButton {
            text-align: left;
            padding: 10px;
            border-width: 0px;
        }
        #menuBarButton {
            border: none;
        }
        QPushButton:hover, QToolButton:hover{
            background-color: rgba(0, 0, 0, 0.3);
        }
        QPushButton:pressed, QToolButton:pressed {
            background-color: rgba(0, 0, 0, 0.4);
        }
        QPushButton:disabled, QToolButton:disabled {
            color: rgba(100, 100, 100, 1);
        }
        QTabWidget::pane {
            border: none;
        }
        QTabBar::tab {
            background-color: rgba(255, 255, 255, 0.05);
        }
        QTabBar::tab:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        QTabBar::tab:selected {
            background-color: rgba(232, 200, 93, 1);
            color: black;
        }
        QTabBar::close-button {
            image: url(Assets/closeIcon.png);
        }
        QGraphicsView {
            border: 5px inset rgba(30, 30, 30, 1);
        }
        #SectionTitle {
            background-color: rgba(0, 0, 0, 0.2);
        }
        #SectionSpacer {
            background-color: rgba(80, 80, 80, 1);
        }
        QComboBox {
            color: white;
            padding: 0 0 0 20px;
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        QComboBox:drop-down {
            width: 32px;
            background-color: transparent;
        }
        QComboBox:down-arrow {
            image: url(Assets/downArrow.png);
            width: 16px;
            height: 16px;
        }
        QComboBox QAbstractItemView::item, QListWidget::item { 
            min-height: 50px; min-width: 50px;
        }
        QListView, QLineEdit {
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        QListView::item:selected { 
            background-color: rgba(0, 0, 0, 0.2);
        }
        #minMaxButton {
            background-color: rgba(0, 0, 0, 0);
            border: none;
            border-radius: 0px 8px 0px 0px;
        }
        #minMaxButton:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        #minMaxButton:pressed {
            background-color: rgba(255, 255, 255, 0.3);
        }
        #chipParameterList QLabel {
            background-color: rgba(255, 255, 255, 0.05);
            text-align: center;
            font-weight: bold;
            padding: 5px 20px 5px 20px;
        }
        #chipParameterList * {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2px;
        }
        #chipParameterList QLabel {
            background-color: rgba(255, 255, 255, 0.1);
        }
        #chipParameterList QSpinBox, QDoubleSpinBox, QCheckBox {
            margin: 5px;
            border: 1px solid white;
            background-color: transparent;
        }
        #chipParameterList QCheckBox {
            border: none;
        }
        #chipParameterList * {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2px;
        }
        #chipParameterList QLabel {
            background-color: rgba(255, 255, 255, 0.1);
        }
        #chipParameterList QSpinBox, QDoubleSpinBox, QCheckBox {
            margin: 5px;
            border: 1px solid white;
            background-color: transparent;
        }
        #chipParameterList QCheckBox {
            border: none;
        }
        #chipValvesList QLabel {
            background-color: rgba(255, 255, 255, 0.05);
            text-align: center;
            font-weight: bold;
            padding: 5px 20px 5px 20px;
        }
        #chipValvesList * {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2px;
        }
        #chipValvesList QLabel {
            background-color: rgba(255, 255, 255, 0.1);
        }
        #chipValvesList QSpinBox, QDoubleSpinBox, QCheckBox {
            margin: 5px;
            border: 1px solid white;
            background-color: transparent;
        }
        #chipValvesList QCheckBox {
            border: none;
        }
        *[valveState=true] {
            background-color: rgba(160, 191, 101, 1);
        }
        *[valveState=false] {
            background-color: rgba(191, 99, 103, 1);
        }
        ImageItem[roundedFrame=true] {
            border-radius: 0px;
        }
        BeginPortWidget *{
            background-color: rgba(255, 255, 255, 0.05);
            border-width: 0px;
            border-top-left-radius:0px;
            border-bottom-left-radius:0px;
            border-bottom-right-radius:0px;
        }
        CompletedPortWidget *{
            background-color: rgba(255, 255, 255, 0.1);
            border-width: 0px;
            border-top-left-radius:0px;
            border-top-right-radius:0px;
            border-bottom-left-radius:0px;
        }
        *[isStart=true] {
            background-color: rgba(20, 100, 20, 0.8);
        }
        *[isActive=true] {
            border: 6px solid rgba(245, 215, 66, 1);
            margin: 0px;
        }
        StepProgressBar {
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 0px;
            background-color: transparent;
        }
        StepProgressBar::chunk {
            background: rgba(245, 215, 66, 1);
        }
        RigConfigurationWindow QListWidget:item:!focus, QListWidget:item:focus {
            color: rgba(200, 200, 200, 1);
            border: none;
        }
        RigConfigurationWindow QListWidget::item:selected {
            color: white;
            border: 2px solid white;
        }
        RigViewWidget QPushButton {
            background-color: transparent;
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 5px;
            text-align: center;
        }
        RigViewWidget QPushButton:checked {
            background-color: rgba(0, 150, 0, 1);
            image: none;
        }
        RigViewWidget QPushButton:hover:!checked {
            background-color: rgba(0, 0, 0, 0.5);
        }
        RigViewWidget QPushButton:hover:checked {
            background-color: rgba(0, 150, 0, 0.5);
        }
        RigViewWidget QPushButton:disabled {
            image: url(Assets/locked.png);
        }
        *[state='HoverAndSelect'] {
            border: 4px solid rgba(52, 222, 235, 1);
            margin: 2px;
        }
        *[state='Select'] {
            border: 2px solid rgba(52, 222, 235, 1);
            margin: 4px;
        }
        *[state='Hover'] {
            border: 2px solid rgba(35, 159, 168, 1);
            margin: 4px;
        }
        *[state='None'] {
            border: 1px solid rgba(30, 30, 30, 1);
            margin: 5px;
        }
        *{
            color: white;
        }
        *[roundedFrame=true] {
            background-color: rgba(30, 30, 30, 1);
            border-radius: """ + str(8) + """
        }
"""
