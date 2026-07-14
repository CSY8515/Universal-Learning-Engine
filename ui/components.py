"""Reusable presentation components for ULE views."""


def render_view_intro(st_module, eyebrow: str, title: str, caption: str) -> None:
    st_module.caption(eyebrow.upper())
    st_module.header(title)
    st_module.write(caption)


def render_empty_state(st_module, title: str, message: str) -> None:
    with st_module.container(border=True):
        st_module.subheader(title)
        st_module.write(message)


def format_percentage(value: object) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.0f}%"
    return "-"


def format_priority(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return "-"
    return value.strip().replace("_", " ").title()
