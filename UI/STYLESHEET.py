stylesheet = """
#Container {
            border-width: 2px;
        }
        *, QTabBar {
            background-color: rgba(65, 65, 65, 1);
            border-color: rgba(80, 80, 80, 1);
            color: rgba(230, 230, 230, 1);
            border-style: solid;
            border-width: 0px;
       } 
       MenuBar {
            border-width: 0px 2px 0px 2px;
       }
        QMenuBar::item:selected, QMenu::item:selected {
            background-color: rgba(0, 0, 0, 0.3);
            color: white;
        }
        QPushButton, QToolButton {
            background-color: rgba(0, 0, 0, 0.05);
            text-align: left;
            padding: 10px;
            border-width: 1px;
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
            background-color: transparent;
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
"""