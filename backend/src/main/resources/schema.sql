DROP TABLE IF EXISTS resumes;
DROP TABLE IF EXISTS chat_bots;

CREATE TABLE resumes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    source VARCHAR(64),
    city VARCHAR(64),
    current_salary VARCHAR(32),
    expected_salary VARCHAR(32),
    gender VARCHAR(16),
    age INT,
    phone VARCHAR(32),
    email VARCHAR(128),
    highest_education VARCHAR(32),
    work_years INT,
    position VARCHAR(128),
    status VARCHAR(32) NOT NULL,
    candidate_status VARCHAR(32),
    communication_status VARCHAR(32),
    intention VARCHAR(64),
    advantages VARCHAR(1024),
    school VARCHAR(128),
    major VARCHAR(128),
    degree VARCHAR(32),
    education_start DATE,
    education_end DATE,
    company VARCHAR(128),
    work_position VARCHAR(128),
    work_start DATE,
    work_end DATE,
    work_description VARCHAR(1024),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    robot_name VARCHAR(64),
    avatar_color VARCHAR(32)
);

CREATE TABLE chat_bots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    wechat_id VARCHAR(64) NOT NULL,
    avatar_url VARCHAR(255),
    status VARCHAR(32) NOT NULL,
    bound_resume_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
