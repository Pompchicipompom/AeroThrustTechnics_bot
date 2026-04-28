from app.models.enums import SubmitMode

MENU_SEND_REPORT = "Отправить сообщение"
MENU_HOW_IT_WORKS = "Как это работает"
MENU_ANON_INFO = "Что значит анонимно"
MENU_HELP = "Помощь"

ACTION_CANCEL = "Отменить"
ACTION_SKIP_ATTACHMENTS = "Пропустить"
ACTION_GO_TO_CONFIRMATION = "К подтверждению"

CALLBACK_MODE_PREFIX = "report_mode:"
CALLBACK_CATEGORY_PREFIX = "report_category:"
CALLBACK_CONFIRM_REPORT = "report_confirm"
CALLBACK_CANCEL_REPORT = "report_cancel"

SUBMIT_MODE_BY_VALUE: dict[str, SubmitMode] = {
    SubmitMode.ANONYMOUS.value: SubmitMode.ANONYMOUS,
    SubmitMode.OPEN.value: SubmitMode.OPEN,
}
