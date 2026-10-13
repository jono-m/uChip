"""How each type of chip element is shown on the canvas and edited in the inspector.

One module per element type (valve, text, image, program) defines both: a view (XView, built by
build_x_view) that the canvas places, and an inspector (XInspector, built by build_x_inspector) that the
inspector panel shows when the element is selected. Each holds its element and whatever else it needs,
and refresh() updates its widgets from them. element_ui.py picks the view and inspector for an element's
type.
"""
