import reflex as rx

class DashboardConfig(rx.Config):
    pass

config = DashboardConfig(
    app_name="dashboard",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)