from app.models.enums import SubmitMode

MENU_SEND_REPORT = "Отправить сообщение"
MENU_HOW_IT_WORKS = "Как это работает"
MENU_REPORT_STATUSES = "Статус обращений"

ACTION_CANCEL = "Отменить"
ACTION_SKIP_ATTACHMENTS = "Пропустить"
ACTION_GO_TO_CONFIRMATION = "К подтверждению"

CALLBACK_MODE_PREFIX = "report_mode:"
CALLBACK_CATEGORY_PREFIX = "report_category:"
CALLBACK_CONFIRM_REPORT = "report_confirm"
CALLBACK_CANCEL_REPORT = "report_cancel"
CALLBACK_USER_REPORTS_LIST = "user_reports:list"
CALLBACK_USER_REPORTS_MENU = "user_reports:menu"
CALLBACK_USER_REPORT_DETAIL_PREFIX = "user_reports:detail:"

SUBMIT_MODE_BY_VALUE: dict[str, SubmitMode] = {
    SubmitMode.ANONYMOUS.value: SubmitMode.ANONYMOUS,
    SubmitMode.OPEN.value: SubmitMode.OPEN,
}
