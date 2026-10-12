import streamlit as st
import json
import os

# 1. НАСТРОЙКИ СТРАНИЦЫ И ТЕМНОГО СТИЛЯ ТЕЛЕМЕТРИИ
st.set_page_config(
    page_title="Race Control",
    layout="wide",
    initial_sidebar_state="expanded"
)

RATINGS = {
    "R": {"bg": "#9333ea", "border": "#9333ea", "text": "#ffffff"},
    "F": {"bg": "#16a34a", "border": "#16a34a", "text": "#ffffff"},
    "M": {"bg": "#eab308", "border": "#eab308", "text": "#000000"},
    "S": {"bg": "#dc2626", "border": "#dc2626", "text": "#ffffff"},
    "D": {"bg": "#78350f", "border": "#78350f", "text": "#ffffff"},
    "-": {"bg": "#27272a", "border": "#27272a", "text": "#71717a"}
}

S1 = ".stApp { background-color: #0b0b0c !important; color: #e4e4e7 !important; }"
S2 = "div[data-testid='stHeader'] { background-color: transparent !important; }"
S3 = ".box-card { background-color: #121214; border: 1px solid #27272a; padding: 8px; }"
S4 = ".sensor-full { background-color: #121214; border: 1px solid #27272a; padding: 8px; }"
S5 = ".sensor-compact { background-color: #121214; padding: 10px; text-align: center; font-weight: 900; }"
S6 = ".rating-badge { position: absolute; top: 6px; right: 6px; width: 18px; height: 18px; font-size: 10px; font-weight: 900; display: flex; align-items: center; justify-content: center; border-radius: 2px; }"

st.markdown(f"<style>{S1}{S2}{S3}{S4}{S5}{S6}</style>", unsafe_allow_html=True)
DB_FILE = "karting_race_state.json"


# 2. ФУНКЦИИ ХРАНЕНИЯ ДАННЫХ ГОНКИ
def save_state():
    state = {
        "step": st.session_state.step,
        "view_mode": st.session_state.view_mode,
        "sensors": st.session_state.sensors,
        "cars": st.session_state.cars,
        "boxes_queue": st.session_state.boxes_queue,
        "repair_list": st.session_state.repair_list
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def load_state():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                st.session_state.step = state["step"]
                st.session_state.view_mode = state.get("view_mode", "Полный")
                st.session_state.sensors = state["sensors"]
                st.session_state.cars = state["cars"]
                st.session_state.boxes_queue = state["boxes_queue"]
                st.session_state.repair_list = state.get("repair_list", [])
                return True
        except:
            return False
    return False


if "step" not in st.session_state:
    if not load_state():
        st.session_state.step = "settings"
        st.session_state.view_mode = "Полный"
        st.session_state.sensors = []
        st.session_state.cars = {}
        st.session_state.boxes_queue = []
        st.session_state.repair_list = []


# 3. ВСПЛЫВАЮЩЕЕ МЕНЮ ДЕЙСТВИЙ (ПРИ КЛИКЕ НА ДАТЧИК)
@st.dialog("Действия")
def show_action_dialog(sensor_id):
    sensor = next(s for s in st.session_state.sensors if s["id"] == sensor_id)
    car_id = sensor["car_id"]
    st.markdown(f"### №{sensor_id} — действия")
    st.markdown(
        f"<div style='background-color:#18181b; padding:8px; text-align:center;'>Сейчас стоит <b>Машина {car_id}</b></div>",
        unsafe_allow_html=True)

    if st.button("⭐ Это мой пилот", use_container_width=True):
        st.info("Пилот отмечен!")
        st.rerun()

    if st.button("🏁 Пит-стоп", type="primary", use_container_width=True):
        if not st.session_state.boxes_queue:
            st.error("В боксах нет свободных машин!")
        else:
            next_car = st.session_state.boxes_queue.pop(0)
            st.session_state.boxes_queue.append(car_id)
            sensor["car_id"] = next_car
            save_state()
            st.rerun()

    if st.button("🔄 Пит-стоп без смены", use_container_width=True):
        st.success("Время зафиксировано!")
        st.rerun()

    st.markdown("---")
    st.write("🔧 **Изменить рейтинг шасси:**")
    current_rating = st.session_state.cars[car_id]["rating"]
    new_rating = st.selectbox("Рейтинг:", options=list(RATINGS.keys()),
                              index=list(RATINGS.keys()).index(current_rating), key="sb_modal_rating",
                              label_visibility="collapsed")
    if new_rating != current_rating:
        st.session_state.cars[car_id]["rating"] = new_rating
        save_state()
        st.rerun()

    if st.button("💥 Поломка на трассе", use_container_width=True):
        if not st.session_state.boxes_queue:
            st.error("Нет подменных машин!")
        else:
            next_car = st.session_state.boxes_queue.pop(0)
            st.session_state.repair_list.append(car_id)
            sensor["car_id"] = next_car
            save_state()
            st.rerun()


# 4. ЛОГИКА ОТОБРАЖЕНИЯ ЭКРАНОВ (IF / ELSE)
if st.session_state.step == "settings":
    st.title("🏁 Инициализация этапа гонки")
    col1, col2 = st.columns(2)
    track_to = col1.number_input(
        "Количество датчиков на трассе:",
        min_value=1, value=40
    )
    boxes_to = col2.number_input(
        "Сколько машин изначально в боксах:",
        min_value=0, value=5
    )
    custom_boxes = st.text_input(
        "Указать специфические номера машин через пробел:",
        value="43C 5C 3K 9K 42C"
    )

    if st.button("🚀 Сгенерировать конфигурацию гонки", use_container_width=True):
        st.session_state.sensors = [
            {"id": str(i), "car_id": str(i)}
            for i in range(1, track_to + 1)
        ]
        for s in st.session_state.sensors:
            st.session_state.cars[s["car_id"]] = {
                "id": s["car_id"], "rating": "-"
            }

        b_queue = []
        if custom_boxes.strip():
            for c_id in custom_boxes.split():
                st.session_state.cars[c_id] = {
                    "id": c_id, "rating": "-"
                }
                b_queue.append(c_id)
        st.session_state.boxes_queue = b_queue
        st.session_state.step = "race"
        save_state()
        st.rerun()

else:
    # БОКОВАЯ ПАНЕЛЬ С ФОРМАМИ ДОБАВЛЕНИЯ И РЕМОНТА
    with st.sidebar:
        st.header("🛠️ Управление парком")

        # ДОБАВЛЕНИЕ С НУЛЯ
        st.subheader("➕ Новая машина")
        new_name = st.text_input("Номер машины:", key="add_new_name")
        new_rating = st.selectbox(
            "Рейтинг:", list(RATINGS.keys()),
            index=5, key="add_new_rating"
        )
        max_pos = len(st.session_state.boxes_queue) + 1
        new_pos = st.number_input(
            "Место на пите:", min_value=1,
            max_value=max_pos, value=max_pos,
            key="add_new_pos"
        )

        if st.button("Добавить в боксы", use_container_width=True):
            if not new_name.strip():
                st.error("Введите номер!")
            elif (new_name in st.session_state.boxes_queue or
                  any(s["car_id"] == new_name
                      for s in st.session_state.sensors)):
                st.error("Карт уже в гонке!")
            else:
                st.session_state.cars[new_name] = {
                    "id": new_name, "rating": new_rating
                }
                st.session_state.boxes_queue.insert(
                    new_pos - 1, new_name
                )
                save_state()
                st.rerun()

        st.markdown("---")

        # ВОЗВРАТ С РЕМОНТА
        st.subheader(f"💥 РЕМЗОНА ({len(st.session_state.repair_list)})")
        if not st.session_state.repair_list:
            st.caption("Машин в ремонте нет.")
        else:
            rep_car = st.selectbox(
                "Из ремонта:", st.session_state.repair_list
            )
            c_r = st.session_state.cars[rep_car]["rating"]
            rep_rating = st.selectbox(
                "Новый рейтинг:", list(RATINGS.keys()),
                index=list(RATINGS.keys()).index(c_r)
            )
            max_rep_pos = len(st.session_state.boxes_queue) + 1
            rep_pos = st.number_input(
                "Место в питах:", min_value=1,
                max_value=max_rep_pos, value=max_rep_pos
            )

            if st.button(
                    "Вернуть в боксы", type="primary",
                    use_container_width=True
            ):
                st.session_state.repair_list.remove(rep_car)
                st.session_state.cars[rep_car]["rating"] = rep_rating
                st.session_state.boxes_queue.insert(
                    rep_pos - 1, rep_car
                )
                save_state()
                st.rerun()

    # ВЕРХНЯЯ ШАПКА УПРАВЛЕНИЯ
    top_col1, top_col2, top_col3 = st.columns(3)
    top_col1.subheader("🏎️ Race Control Panel")

    mode = top_col2.radio(
        "Режим:", ["Полный", "Компакт"],
        horizontal=True, label_visibility="collapsed"
    )
    st.session_state.view_mode = mode

    if top_col3.button("🔄 Сбросить гонку"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.step = "settings"
        st.rerun()

    st.markdown("---")

    # СЕТКА: В БОКСАХ
    st.markdown(
        f"### В БОКСАХ <span style='color:#71717a;'>"
        f"{len(st.session_state.boxes_queue)}</span>",
        unsafe_allow_html=True
    )

    box_cols = st.columns(6)
    for b_idx, car_id in enumerate(st.session_state.boxes_queue):
        col = box_cols[b_idx % 6]
        car_data = st.session_state.cars.get(car_id, {"rating": "-"})
        r_style = RATINGS.get(car_data["rating"], RATINGS["-"])
        is_first = b_idx == 0

        badge_html = ""
        if car_data["rating"] != "-":
            badge_html = (
                f'<div class="rating-badge" style="background-color:'
                f'{r_style["bg"]};color:{r_style["text"]};">'
                f'{car_data["rating"]}</div>'
            )

        lbl = (
            '<div style="color:#f97316; font-size:10px; '
            'font-weight:900;">1-я / свободная</div>' if is_first
            else '<div style="color:#71717a; font-size:10px;">'
                 'свободная</div>'
        )
        border_color = "#f97316" if is_first else "#27272a"

        with col:
            st.markdown(
                f'<div class="box-card" style="border-color:'
                f'{border_color};">{badge_html}<div style='
                f'"font-weight:900;">Маш. {car_id}</div>'
                f'{lbl}</div>',
                unsafe_allow_html=True
            )
            if st.button(
                    "На ремонт", key=f"rep_{car_id}",
                    use_container_width=True
            ):
                st.session_state.boxes_queue.remove(car_id)
                st.session_state.repair_list.append(car_id)
                save_state()
                st.rerun()

    st.markdown("---")

    # СЕТКА: НА ТРАССЕ
    st.markdown(
        f"### НА ТРАССЕ <span style='color:#71717a;'>"
        f"{len(st.session_state.sensors)}</span>",
        unsafe_allow_html=True
    )

    grid_count = 6 if st.session_state.view_mode == "Полный" else 10
    track_cols = st.columns(grid_count)

    for idx, sensor in enumerate(st.session_state.sensors):
        col = track_cols[idx % grid_count]
        s_id = sensor["id"]
        car_id = sensor["car_id"]
        car_data = st.session_state.cars.get(car_id, {"rating": "-"})
        r_style = RATINGS.get(car_data["rating"], RATINGS["-"])

        with col:
            if st.session_state.view_mode == "Полный":
                badge_html = ""
                if car_data["rating"] != "-":
                    badge_html = (
                        f'<div class="rating-badge" style='
                        f'"background-color:{r_style["bg"]};'
                        f'color:{r_style["text"]};">'
                        f'{car_data["rating"]}</div>'
                    )
                st.markdown(
                    f'<div class="sensor-full" style="'
                    f'border-top:3px solid {r_style["border"]};">'
                    f'{badge_html}<div style="font-size:24px; '
                    f'font-weight:900;">{s_id}</div>'
                    f'<div style="font-size:11px; '
                    f'color:#a1a1aa;">Машина {car_id}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="sensor-compact" style="'
                    f'border:2px solid {r_style["border"]};'
                    f'color:#fff;">{s_id}</div>',
                    unsafe_allow_html=True
                )

            if st.button(
                    "⚙️", key=f"act_{s_id}",
                    use_container_width=True
            ):
                show_action_dialog(s_id)
