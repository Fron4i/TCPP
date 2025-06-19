import getpass
import os
import json
from datetime import datetime

USERS = {
    'teacher1': {'password': '111', 'role': 'teacher'},
    'student1': {'password': '222', 'role': 'student'},
    'student2': {'password': 'pass3', 'role': 'student'},
}
STORAGE = 'storage.json'

def load_data():
    if os.path.exists(STORAGE):
        data = json.load(open(STORAGE, encoding='utf-8'))
    else:
        data = {}
    data.setdefault('sessions', {})    # {subject: [session_str, ...]}
    data.setdefault('attendance', {})  # {subject: {session: [student,...]}}
    data.setdefault('grades', {})      # {subject: {session: {student:grade}}}
    data.setdefault('documents', {})   # {student: [{'name','status'}, ...]}
    # ensure inner dicts
    for subj, sess_list in data['sessions'].items():
        data['attendance'].setdefault(subj, {})
        data['grades'].setdefault(subj, {})
        for sess in sess_list:
            data['attendance'][subj].setdefault(sess, [])
            data['grades'][subj].setdefault(sess, {})
    return data

def save_data(data):
    with open(STORAGE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def login():
    while True:
        print("====== Вход ======")
        u = input("Логин: ")
        p = getpass.getpass("Пароль: ")
        info = USERS.get(u)
        if info and info['password'] == p:
            return u, info['role']
        print("Неверные данные, попробуйте ещё раз.\n")

def choose_subject(data, allow_add=False):
    subs = list(data['sessions'].keys())
    while True:
        print("------ Предметы ------")
        for i, s in enumerate(subs, 1):
            print(f"{i}. {s}")
        if allow_add:
            print(f"{len(subs)+1}. Добавить новый предмет")
        print("0. Назад")
        choice = input("Выбор: ")
        if choice == '0':
            return None
        try:
            idx = int(choice)
        except ValueError:
            print("Неверный ввод.")
            continue
        if allow_add and idx == len(subs)+1:
            name = input("Название предмета: ")
            data['sessions'][name] = []
            data['attendance'][name] = {}
            data['grades'][name] = {}
            save_data(data)
            return name
        if 1 <= idx <= len(subs):
            return subs[idx-1]
        print("Неверный номер.")

def choose_session(data, subj, allow_add=False):
    sess_list = data['sessions'][subj]
    while True:
        print("------ Пары ------")
        for i, s in enumerate(sess_list, 1):
            print(f"{i}. {s}")
        if allow_add:
            print(f"{len(sess_list)+1}. Создать новую пару")
        print("0. Назад")
        choice = input("Выбор: ")
        if choice == '0':
            return None
        try:
            idx = int(choice)
        except ValueError:
            print("Неверный ввод.")
            continue
        if allow_add and idx == len(sess_list)+1:
            name = input("Название пары: ")
            date_input = input("Дата и время (ДД.MM.ГГГГ ЧЧ:ММ): ")
            try:
                dt = datetime.strptime(date_input, "%d.%m.%Y %H:%M")
            except ValueError:
                print("Неверный формат даты.")
                continue
            s = f"{name} [{dt.strftime('%d.%m.%Y %H:%M')}]"
            sess_list.append(s)
            data['attendance'][subj][s] = []
            data['grades'][subj][s] = {}
            save_data(data)
            return s
        if 1 <= idx <= len(sess_list):
            return sess_list[idx-1]
        print("Неверный номер.")

def attendance_menu_teacher(data):
    all_students = [u for u,i in USERS.items() if i['role']=='student']
    while True:
        print("\n=== Посещаемость (преподаватель) ===")
        print(f"{'Предмет':<12} {'Пара':<25} {'П':<3} {'Н':<3}")
        for subj, sess_list in data['sessions'].items():
            for sess in sess_list:
                marked = data['attendance'][subj][sess]
                not_marked = [s for s in all_students if s not in marked]
                print(f"{subj:<12} {sess:<25} {len(marked):<3} {len(not_marked):<3}")
        print("\n1. Изменить посещаемость")
        print("0. Назад")
        cmd = input("> ")
        if cmd == '1':
            subj = choose_subject(data, allow_add=True)
            if not subj: continue
            sess = choose_session(data, subj, allow_add=True)
            if not sess: continue
            marked = data['attendance'][subj][sess]
            while True:
                print("\nСтатус посещаемости:")
                for idx, stud in enumerate(all_students, 1):
                    status = 'П' if stud in marked else 'Н'
                    print(f"{idx}. {stud:<10} [{status}]")
                print("0. Готово")
                choice = input("Номер студента для переключения: ")
                if choice == '0':
                    break
                try:
                    i = int(choice) - 1
                    stud = all_students[i]
                except:
                    print("Неверный ввод.")
                    continue
                if stud in marked:
                    marked.remove(stud)
                    print(f"❌ {stud} теперь Н")
                else:
                    marked.append(stud)
                    print(f"✅ {stud} теперь П")
                save_data(data)
        elif cmd == '0':
            break
        else:
            print("Неверная команда.")

def grades_menu_teacher(data):
    all_students = [u for u,i in USERS.items() if i['role']=='student']
    while True:
        print("\n=== Оценки (преподаватель) ===")
        print(f"{'Предмет':<12} {'Пара':<25} " + ' '.join(f"{s:<8}" for s in all_students))
        for subj, sess_list in data['sessions'].items():
            for sess in sess_list:
                gmap = data['grades'][subj][sess]
                grades_row = ' '.join(f"{gmap.get(s,'-'):<8}" for s in all_students)
                print(f"{subj:<12} {sess:<25} {grades_row}")
        print("\n1. Изменить оценки")
        print("0. Назад")
        cmd = input("> ")
        if cmd == '1':
            subj = choose_subject(data, allow_add=True)
            if not subj: continue
            sess = choose_session(data, subj, allow_add=True)
            if not sess: continue
            grades_map = data['grades'][subj][sess]
            while True:
                print("\nТекущие оценки:")
                for idx, stud in enumerate(all_students, 1):
                    print(f"{idx}. {stud:<10} [{grades_map.get(stud,'-')}]")
                print("0. Готово")
                choice = input("Номер студента для редактирования: ")
                if choice == '0':
                    break
                try:
                    i = int(choice) - 1
                    stud = all_students[i]
                except:
                    print("Неверный ввод.")
                    continue
                new = input(f"Новая оценка для {stud} (enter — убрать): ")
                if new == '':
                    if stud in grades_map:
                        del grades_map[stud]
                        print(f"❌ Оценка {stud} удалена")
                else:
                    try:
                        g = int(new)
                        grades_map[stud] = g
                        print(f"✅ {stud} = {g}")
                    except:
                        print("Неверный формат.")
                save_data(data)
        elif cmd == '0':
            break
        else:
            print("Неверная команда.")

def documents_menu_teacher(data):
    while True:
        print("\n=== Документы (преподаватель) ===")
        print(f"{'Студент':<10} {'Документ':<20} {'Статус'}")
        for u, docs in data['documents'].items():
            for d in docs:
                print(f"{u:<10} {d['name']:<20} {d['status']}")
        print("\n1. Утвердить/Отклонить")
        print("0. Назад")
        cmd = input("> ")
        if cmd == '1':
            pending = [(u,d) for u,docs in data['documents'].items() for d in docs if d['status']=='pending']
            if not pending:
                print("Нет pending-документов.")
                continue
            for idx, (u,d) in enumerate(pending,1):
                print(f"{idx}. {u} — {d['name']}")
            print("0. Назад")
            choice = input("Выбор: ")
            if choice == '0':
                continue
            try:
                i = int(choice)-1
                u,d = pending[i]
            except:
                print("Неверный ввод.")
                continue
            act = input("a=утвердить, r=отклонить: ")
            if act=='a':
                d['status']='approved'; print("✅ Утверждено")
            elif act=='r':
                d['status']='rejected'; print("❌ Отклонено")
            else:
                print("Пропущено")
            save_data(data)
        elif cmd == '0':
            break
        else:
            print("Неверная команда.")

def teacher_menu(data):
    while True:
        print("\n============================")
        print("  МЕНЮ ПРЕПОДАВАТЕЛЯ")
        print("============================")
        print("1. Посещаемость")
        print("2. Оценки")
        print("3. Документы")
        print("0. Выход")
        cmd = input("> ")
        if cmd == '1':
            attendance_menu_teacher(data)
        elif cmd == '2':
            grades_menu_teacher(data)
        elif cmd == '3':
            documents_menu_teacher(data)
        elif cmd == '0':
            break
        else:
            print("Неверная команда.")

def attendance_menu_student(data, user):
    while True:
        print("\n=== Моя посещаемость ===")
        for subj, sess_list in data['sessions'].items():
            for sess in sess_list:
                mark = '✓' if user in data['attendance'][subj][sess] else ' '
                print(f"{subj:<12} {sess:<25} {mark}")
        print("\n1. Отметиться")
        print("0. Назад")
        cmd = input("> ")
        if cmd == '1':
            subj = choose_subject(data)
            if not subj: continue
            sess = choose_session(data, subj)
            if not sess: continue
            if user in data['attendance'][subj][sess]:
                print("Вы уже отмечены.")
            else:
                data['attendance'][subj][sess].append(user)
                save_data(data)
                print("✅ Отметились")
        elif cmd == '0':
            break
        else:
            print("Неверная команда.")

def grades_menu_student(data, user):
    print("\n=== Мои оценки ===")
    found = False
    for subj, sess_list in data['sessions'].items():
        for sess in sess_list:
            g = data['grades'][subj][sess].get(user)
            if g is not None:
                print(f"{subj:<12} {sess:<25} {g}")
                found = True
    if not found:
        print("Оценок нет.")
    input("Enter, чтобы вернуться.")

def documents_menu_student(data, user):
    while True:
        print("\n=== Мои документы ===")
        docs = data['documents'].get(user, [])
        if docs:
            for d in docs:
                print(f"{d['name']:<20} {d['status']}")
        else:
            print("Документов нет.")
        print("\n1. Подать документ")
        print("0. Назад")
        cmd = input("> ")
        if cmd == '1':
            name = input("Имя файла: ")
            data['documents'].setdefault(user, []).append({'name':name,'status':'pending'})
            save_data(data)
            print("✅ Подано")
        elif cmd == '0':
            break
        else:
            print("Неверная команда.")

def student_menu(data, user):
    while True:
        print("\n============================")
        print("   МЕНЮ СТУДЕНТА")
        print("============================")
        print("1. Посещаемость")
        print("2. Документы")
        print("3. Оценки")
        print("0. Выход")
        cmd = input("> ")
        if cmd == '1':
            attendance_menu_student(data, user)
        elif cmd == '2':
            documents_menu_student(data, user)
        elif cmd == '3':
            grades_menu_student(data, user)
        elif cmd == '0':
            break
        else:
            print("Неверная команда.")

def main():
    data = load_data()
    user, role = login()
    if role == 'teacher':
        teacher_menu(data)
    else:
        student_menu(data, user)

if __name__ == '__main__':
    main()
# изменения второго разработчика
