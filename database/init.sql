CREATE TABLE Contacts (
    contact_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(10) NOT NULL CHECK (role IN ('client', 'staff')),
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE Requests (
    request_id SERIAL PRIMARY KEY,
    contact_id INT NOT NULL,
    preferred_time TIMESTAMP,
    notes TEXT,
    status VARCHAR(15) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT REFERENCES Contacts(contact_id),
    reviewed_at TIMESTAMP,
    CONSTRAINT fk_request_contact 
        FOREIGN KEY (contact_id) 
        REFERENCES Contacts(contact_id) 
        ON DELETE CASCADE
);

CREATE TABLE Appointments (
    appointment_id SERIAL PRIMARY KEY,
    contact_id INT NOT NULL,
    staff_id INT,
    request_id INT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(15) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_appointment_contact 
        FOREIGN KEY (contact_id) 
        REFERENCES Contacts(contact_id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_appointment_request 
        FOREIGN KEY (request_id) 
        REFERENCES Requests(request_id) 
        ON DELETE SET NULL
);

CREATE TABLE Notifications (
    notification_id SERIAL PRIMARY KEY,
    appointment_id INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    sent_to VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(15) NOT NULL CHECK (status IN ('sent', 'failed')),
    CONSTRAINT fk_notification_appointment 
        FOREIGN KEY (appointment_id) 
        REFERENCES Appointments(appointment_id) 
        ON DELETE CASCADE
);

INSERT INTO Contacts (full_name, email, phone, role, username, password_hash)
VALUES ('Tester', 'testemail@yahoo.com', '0000000000', 'staff', 'admin', 'scrypt:32768:8:1$KaR74yZsn2UPcPG4$1ba516284925eb72f4f50dee34c9871791f2efb4914adc5bc3b9533d6804445fc8ac5bad7b41f26a719bdc852f0c3d581dc096eff842f0b36729394fbf45d911');
