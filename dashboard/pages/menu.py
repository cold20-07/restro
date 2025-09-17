"""Menu management page for restaurant dashboard"""

import reflex as rx
from typing import List, Dict, Any, Optional
from dashboard.state import MenuState
from dashboard.components import loading_spinner, empty_state, error_message


def menu_page() -> rx.Component:
    """Menu management page with CRUD operations"""
    from dashboard.layout import base_layout
    
    # Set current page for navigation
    from dashboard.state import NavigationState
    NavigationState.current_page = "menu"
    
    return base_layout(
        content=rx.vstack(
            # Load menu data on page mount
            rx.script("window.addEventListener('load', () => { MenuState.load_menu_items(); });"),
            
            # Menu filters and categories
            menu_filters(),
            
            # Menu items grid
            menu_items_grid(),
            
            # Add/Edit item modal
            menu_item_modal(),
            
            spacing="6",
            width="100%"
        ),
        page_title="Menu Management"
    )


def menu_filters() -> rx.Component:
    """Filters and search controls for menu items"""
    return rx.card(
        rx.hstack(
            # Search input
            rx.input(
                placeholder="Search menu items...",
                size="3",
                width="300px"
            ),
            
            # Category filter
            rx.select(
                ["All Categories", "Appetizers", "Main Course", "Pizza", "Pasta", "Salads", "Desserts", "Beverages"],
                placeholder="All Categories",
                size="3"
            ),
            
            # Availability filter
            rx.select(
                ["All Items", "Available Only", "Unavailable Only"],
                placeholder="All Items",
                size="3"
            ),
            
            rx.spacer(),
            
            # Quick stats
            rx.hstack(
                quick_menu_stat("Total Items", "25"),
                quick_menu_stat("Available", "22"),
                quick_menu_stat("Categories", "6"),
                spacing="6"
            ),
            
            spacing="4",
            align="center",
            width="100%"
        ),
        padding="6",
        width="100%"
    )


def quick_menu_stat(label: str, value) -> rx.Component:
    """Quick stat component for menu overview"""
    return rx.vstack(
        rx.text(value, font_size="lg", font_weight="bold", color="gray.900"),
        rx.text(label, font_size="sm", color="gray.600"),
        spacing="1",
        align="center"
    )


def menu_items_grid() -> rx.Component:
    """Grid layout for menu items"""
    return rx.cond(
        MenuState.is_loading,
        rx.center(
            loading_spinner("lg"),
            height="400px",
            width="100%"
        ),
        rx.cond(
            MenuState.error_message != "",
            rx.center(
                error_message(MenuState.error_message),
                height="400px",
                width="100%"
            ),
            rx.cond(
                False,
                rx.center(
                    empty_state(
                        "utensils",
                        "No menu items found",
                        "Add your first menu item to get started"
                    ),
                    height="400px",
                    width="100%"
                ),
                rx.grid(
                    simple_menu_item_card("Margherita Pizza", "Classic pizza with tomato sauce, mozzarella, and fresh basil", "15.00", "Pizza", True),
                    simple_menu_item_card("Caesar Salad", "Fresh romaine lettuce with Caesar dressing, croutons, and parmesan", "12.00", "Salads", True),
                    simple_menu_item_card("Grilled Chicken", "Tender grilled chicken breast with herbs and spices", "20.00", "Main Course", True),
                    simple_menu_item_card("Pasta Carbonara", "Creamy pasta with bacon, eggs, and parmesan cheese", "15.00", "Pasta", False),
                    columns="4",
                    spacing="6",
                    width="100%"
                )
            )
        )
    )


def simple_menu_item_card(name: str, description: str, price: str, category: str, is_available: bool) -> rx.Component:
    """Simple static menu item card for demo"""
    return rx.card(
        rx.vstack(
            # Item image placeholder
            rx.center(
                rx.icon(tag="image", size=32, color="gray.400"),
                width="100%",
                height="150px",
                background="gray.100",
                border_radius="md"
            ),
            
            # Item details
            rx.vstack(
                rx.hstack(
                    rx.text(name, font_size="lg", font_weight="semibold", color="gray.900"),
                    rx.spacer(),
                    rx.switch(
                        checked=is_available,
                        color_scheme="green" if is_available else "gray",
                        size="2"
                    ),
                    justify="between",
                    width="100%"
                ),
                
                rx.text(description, font_size="sm", color="gray.600", line_height="1.4"),
                
                rx.hstack(
                    rx.badge(category, color_scheme="blue", size="2"),
                    rx.spacer(),
                    rx.text(f"${price}", font_size="lg", font_weight="bold", color="#FF6B35"),
                    justify="between",
                    width="100%"
                ),
                
                # Action buttons
                rx.hstack(
                    rx.button(
                        rx.icon(tag="pencil", size=14),
                        "Edit",
                        size="2",
                        variant="outline",
                        color_scheme="gray"
                    ),
                    rx.button(
                        rx.icon(tag="trash_2", size=14),
                        "Delete",
                        size="2",
                        variant="outline",
                        color_scheme="red"
                    ),
                    spacing="2",
                    width="100%"
                ),
                
                spacing="3",
                align="start",
                width="100%"
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="4",
        width="100%",
        _hover={"box_shadow": "md", "transform": "translateY(-2px)", "transition": "all 0.2s"}
    )


def menu_item_card(item) -> rx.Component:
    """Individual menu item card with actions"""
    return rx.card(
        rx.vstack(
            # Item image placeholder
            rx.box(
                rx.cond(
                    item["image_url"] != "",
                    rx.image(
                        src=item["image_url"],
                        width="100%",
                        height="150px",
                        object_fit="cover",
                        border_radius="md"
                    ),
                    rx.center(
                        rx.icon(tag="image", size=32, color="gray.400"),
                        width="100%",
                        height="150px",
                        background="gray.100",
                        border_radius="md"
                    )
                ),
                width="100%"
            ),
            
            # Item details
            rx.vstack(
                rx.hstack(
                    rx.text(item["name"], font_size="lg", font_weight="semibold", color="gray.900"),
                    rx.spacer(),
                    availability_toggle(item["id"], item["is_available"]),
                    justify="between",
                    width="100%"
                ),
                
                rx.text(item["description"], font_size="sm", color="gray.600", line_height="1.4"),
                
                rx.hstack(
                    rx.badge(item["category"], color_scheme="blue", size="2"),
                    rx.spacer(),
                    rx.text(f"${item['price']:.2f}", font_size="lg", font_weight="bold", color="#FF6B35"),
                    justify="between",
                    width="100%"
                ),
                
                # Action buttons
                rx.hstack(
                    rx.button(
                        rx.icon(tag="pencil", size=14),
                        "Edit",
                        size="2",
                        variant="outline",
                        color_scheme="gray",
                        on_click=lambda: MenuState.open_edit_item_modal(item["id"])
                    ),
                    rx.button(
                        rx.icon(tag="trash_2", size=14),
                        "Delete",
                        size="2",
                        variant="outline",
                        color_scheme="red",
                        on_click=lambda: MenuState.delete_menu_item(item["id"])
                    ),
                    spacing="2",
                    width="100%"
                ),
                
                spacing="3",
                align="start",
                width="100%"
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="4",
        width="100%",
        _hover={"box_shadow": "md", "transform": "translateY(-2px)", "transition": "all 0.2s"}
    )


def availability_toggle(item_id: str, is_available: bool) -> rx.Component:
    """Toggle switch for item availability"""
    return rx.switch(
        checked=is_available,
        on_change=lambda checked: MenuState.toggle_item_availability(item_id, checked),
        color_scheme="green" if is_available else "gray",
        size="2"
    )


def menu_item_modal() -> rx.Component:
    """Modal for adding/editing menu items"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Add New Menu Item"),
            
            rx.dialog.description(
                "Fill in the details for your menu item"
            ),
            
            # Form fields
            rx.vstack(
                # Item name
                rx.vstack(
                    rx.text("Item Name", font_size="sm", font_weight="medium", color="gray.700"),
                    rx.input(
                        placeholder="Enter item name",
                        size="3",
                        width="100%"
                    ),
                    spacing="2",
                    align="start",
                    width="100%"
                ),
                
                # Description
                rx.vstack(
                    rx.text("Description", font_size="sm", font_weight="medium", color="gray.700"),
                    rx.text_area(
                        placeholder="Enter item description",
                        size="3",
                        width="100%",
                        rows="3"
                    ),
                    spacing="2",
                    align="start",
                    width="100%"
                ),
                
                # Price and Category row
                rx.hstack(
                    rx.vstack(
                        rx.text("Price", font_size="sm", font_weight="medium", color="gray.700"),
                        rx.input(
                            placeholder="0.00",
                            type="number",
                            step="0.01",
                            min="0",
                            size="3",
                            width="100%"
                        ),
                        spacing="2",
                        align="start",
                        width="50%"
                    ),
                    
                    rx.vstack(
                        rx.text("Category", font_size="sm", font_weight="medium", color="gray.700"),
                        rx.select(
                            ["Appetizers", "Main Course", "Pizza", "Pasta", "Salads", "Desserts", "Beverages"],
                            placeholder="Select category",
                            size="3",
                            width="100%"
                        ),
                        spacing="2",
                        align="start",
                        width="50%"
                    ),
                    
                    spacing="4",
                    width="100%"
                ),
                
                # Image URL
                rx.vstack(
                    rx.text("Image URL (optional)", font_size="sm", font_weight="medium", color="gray.700"),
                    rx.input(
                        placeholder="https://example.com/image.jpg",
                        size="3",
                        width="100%"
                    ),
                    spacing="2",
                    align="start",
                    width="100%"
                ),
                
                # Availability checkbox
                rx.hstack(
                    rx.checkbox(
                        "Available for ordering",
                        checked=True,
                        size="2"
                    ),
                    width="100%"
                ),
                
                spacing="4",
                width="100%"
            ),
            
            # Action buttons
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        size="3",
                        variant="outline",
                        color_scheme="gray"
                    )
                ),
                rx.button(
                    "Add Item",
                    size="3",
                    color_scheme="orange"
                ),
                spacing="3",
                justify="end",
                width="100%"
            ),
            
            spacing="6",
            width="500px"
        ),
        open=False
    )