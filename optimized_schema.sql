-- ========================================
-- ОПТИМИЗИРОВАННАЯ СХЕМА БД
-- Образовательный центр
-- ========================================

-- Удаление старых таблиц (если нужен полный reset)
-- DROP TABLE IF EXISTS registrations_active;
-- DROP TABLE IF EXISTS registrations_trial;
-- DROP TABLE IF EXISTS registrations_studying;
-- DROP TABLE IF EXISTS registrations_frozen;
-- DROP TABLE IF EXISTS registrations_payment;
-- DROP TABLE IF EXISTS registrations_completed;
-- DROP TABLE IF EXISTS registrations_other;

-- ========================================
-- СПРАВОЧНЫЕ ТАБЛИЦЫ (DICTIONARIES)
-- ========================================

-- Типы обучения
CREATE TABLE IF NOT EXISTS training_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO training_types (name, description) VALUES
    ('Групповые занятия (80 минут)', 'Занятия в группе до 10 человек'),
    ('Индивидуальное обучение (1 час)', 'Индивидуальные занятия с преподавателем'),
    ('Групповые занятия (60 минут)', 'Занятия в группе до 15 человек');

-- Расписания
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    time_start TEXT,
    time_end TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schedules (name, time_start, time_end) VALUES
    ('Утренняя группа', '09:00', '11:00'),
    ('Обеденная группа', '12:00', '14:00'),
    ('Вечерняя группа', '18:00', '20:00');

-- Статусы студентов
CREATE TABLE IF NOT EXISTS student_statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO student_statuses (code, name, description) VALUES
    ('active', 'Активные', 'Активно проходят обучение'),
    ('trial', 'Пробный урок', 'Записаны на пробный урок'),
    ('studying', 'Обучаются', 'Проходят полный курс'),
    ('frozen', 'Заморожены', 'Временно приостановили обучение'),
    ('waiting_payment', 'Ожидание оплаты', 'Ожидают оплату за курс'),
    ('completed', 'Завершили', 'Успешно завершили курс');

-- ========================================
-- ОСНОВНЫЕ СУЩНОСТИ
-- ========================================

-- Пользователи (единая таблица для всех пользователей бота)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

-- Администраторы (расширение users)
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'admin', -- admin, super_admin, moderator
    permissions TEXT, -- JSON с правами доступа
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_admins_user_id ON admins(user_id);

-- Преподаватели
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    specialization TEXT,
    experience TEXT,
    bio TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_teachers_active ON teachers(is_active);

-- Курсы
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    duration_months INTEGER,
    lessons_count INTEGER,
    price_group INTEGER, -- Цена в тийинах для группового
    price_individual INTEGER, -- Цена в тийинах для индивидуального
    level TEXT, -- beginner, intermediate, advanced
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_courses_active ON courses(is_active);

INSERT OR IGNORE INTO courses (name, description, duration_months, lessons_count, price_group, price_individual, level) VALUES
    ('🇯🇵 Японский язык', 'Изучение японского языка с нуля', 12, 48, 550000, 1300000, 'beginner'),
    ('🇬🇧 Английский язык', 'Изучение английского языка с нуля', 12, 48, 450000, 1200000, 'beginner');

-- Группы
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE SET NULL,
    max_students INTEGER DEFAULT 10,
    current_students INTEGER DEFAULT 0,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_groups_course ON groups(course_id);
CREATE INDEX IF NOT EXISTS idx_groups_teacher ON groups(teacher_id);
CREATE INDEX IF NOT EXISTS idx_groups_active ON groups(is_active);

-- ========================================
-- СТУДЕНТЫ И РЕГИСТРАЦИИ
-- ========================================

-- Регистрации (заявки на обучение)
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    training_type_id INTEGER REFERENCES training_types(id) ON DELETE SET NULL,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE SET NULL,
    status_code TEXT DEFAULT 'active' REFERENCES student_statuses(code),

    -- Временные метки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consultation_time TIMESTAMP NULL,
    trial_lesson_time TIMESTAMP NULL,
    enrollment_date TIMESTAMP NULL,

    -- Уведомления
    notified BOOLEAN DEFAULT 0,
    reminder_sent BOOLEAN DEFAULT 0,

    -- Метаданные
    source TEXT, -- откуда пришла заявка (telegram, web, phone)
    notes TEXT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(user_id);
CREATE INDEX IF NOT EXISTS idx_registrations_status ON registrations(status_code);
CREATE INDEX IF NOT EXISTS idx_registrations_course ON registrations(course_id);
CREATE INDEX IF NOT EXISTS idx_registrations_created ON registrations(created_at);

-- Студенты (те, кто прошел регистрацию и зачислен)
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_code TEXT UNIQUE, -- уникальный код студента
    enrollment_date DATE DEFAULT CURRENT_DATE,
    graduation_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_students_user ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_code ON students(student_code);

-- Связь студентов с группами (many-to-many)
CREATE TABLE IF NOT EXISTS student_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    registration_id INTEGER REFERENCES registrations(id) ON DELETE SET NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status TEXT DEFAULT 'active', -- active, frozen, completed, dropped
    UNIQUE(student_id, group_id)
);

CREATE INDEX IF NOT EXISTS idx_student_groups_student ON student_groups(student_id);
CREATE INDEX IF NOT EXISTS idx_student_groups_group ON student_groups(group_id);
CREATE INDEX IF NOT EXISTS idx_student_groups_status ON student_groups(status);

-- ========================================
-- УЧЕБНЫЙ ПРОЦЕСС
-- ========================================

-- Уроки
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    description TEXT,
    lesson_date DATE NOT NULL,
    lesson_time TEXT, -- время начала урока
    duration_minutes INTEGER DEFAULT 60,
    materials TEXT, -- ссылки на материалы
    homework TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lessons_group ON lessons(group_id);
CREATE INDEX IF NOT EXISTS idx_lessons_teacher ON lessons(teacher_id);
CREATE INDEX IF NOT EXISTS idx_lessons_date ON lessons(lesson_date);

-- Посещаемость
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'present', -- present, absent, late, excused
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lesson_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_attendance_lesson ON attendance(lesson_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);

-- Прогресс студента
CREATE TABLE IF NOT EXISTS student_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lessons_attended INTEGER DEFAULT 0,
    lessons_total INTEGER DEFAULT 0,
    progress_percent REAL DEFAULT 0.0,
    current_level TEXT,
    grade TEXT, -- A, B, C, D, F
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_progress_student ON student_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_progress_course ON student_progress(course_id);

-- ========================================
-- ОБРАТНАЯ СВЯЗЬ И НАПОМИНАНИЯ
-- ========================================

-- Отзывы
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    registration_id INTEGER REFERENCES registrations(id) ON DELETE SET NULL,
    course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_course ON feedback(course_id);
CREATE INDEX IF NOT EXISTS idx_feedback_teacher ON feedback(teacher_id);

-- Напоминания
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    due_date TIMESTAMP NOT NULL,
    sent BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(due_date);
CREATE INDEX IF NOT EXISTS idx_reminders_sent ON reminders(sent);

-- ========================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЗАЦИИ
-- ========================================

-- Автоматическое обновление updated_at
CREATE TRIGGER IF NOT EXISTS update_registrations_timestamp
AFTER UPDATE ON registrations
BEGIN
    UPDATE registrations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_users_timestamp
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Автоматическое обновление счетчика студентов в группе
CREATE TRIGGER IF NOT EXISTS increment_group_students
AFTER INSERT ON student_groups
WHEN NEW.status = 'active'
BEGIN
    UPDATE groups
    SET current_students = current_students + 1
    WHERE id = NEW.group_id;
END;

CREATE TRIGGER IF NOT EXISTS decrement_group_students
AFTER UPDATE ON student_groups
WHEN OLD.status = 'active' AND NEW.status != 'active'
BEGIN
    UPDATE groups
    SET current_students = current_students - 1
    WHERE id = NEW.group_id;
END;

-- Автоматическое создание student_code
CREATE TRIGGER IF NOT EXISTS generate_student_code
AFTER INSERT ON students
WHEN NEW.student_code IS NULL
BEGIN
    UPDATE students
    SET student_code = 'STU' || printf('%06d', NEW.id)
    WHERE id = NEW.id;
END;

-- ========================================
-- ПРЕДСТАВЛЕНИЯ (VIEWS) ДЛЯ УДОБСТВА
-- ========================================

-- Полная информация о студентах
CREATE VIEW IF NOT EXISTS v_students_full AS
SELECT
    s.id,
    s.student_code,
    u.telegram_id,
    u.username,
    u.full_name,
    u.phone,
    u.email,
    s.enrollment_date,
    s.is_active,
    GROUP_CONCAT(DISTINCT g.name) as groups,
    GROUP_CONCAT(DISTINCT c.name) as courses
FROM students s
JOIN users u ON s.user_id = u.id
LEFT JOIN student_groups sg ON s.id = sg.student_id AND sg.status = 'active'
LEFT JOIN groups g ON sg.group_id = g.id
LEFT JOIN courses c ON g.course_id = c.id
GROUP BY s.id;

-- Статистика по группам
CREATE VIEW IF NOT EXISTS v_group_stats AS
SELECT
    g.id,
    g.name as group_name,
    c.name as course_name,
    t.name as teacher_name,
    g.current_students,
    g.max_students,
    ROUND(CAST(g.current_students AS REAL) / g.max_students * 100, 2) as occupancy_percent,
    g.is_active
FROM groups g
LEFT JOIN courses c ON g.course_id = c.id
LEFT JOIN teachers t ON g.teacher_id = t.id;

-- Статистика по регистрациям
CREATE VIEW IF NOT EXISTS v_registration_stats AS
SELECT
    DATE(created_at) as date,
    status_code,
    COUNT(*) as count
FROM registrations
GROUP BY DATE(created_at), status_code;

-- ========================================
-- КОНЕЦ СХЕМЫ
-- ========================================