CREATE DATABASE IF NOT EXISTS grad_applicant_system;
USE grad_applicant_system;

-- Physical Database
CREATE TABLE Applicant (
    UserID INT PRIMARY KEY,
    ApplicantName VARCHAR(100) NOT NULL,
    UndergraduateGPA DECIMAL(3,2),
    DegreeEarned VARCHAR(100)
);

CREATE TABLE Program (
    ProgramID INT PRIMARY KEY,
    ProgramMajor VARCHAR(100) NOT NULL
);

CREATE TABLE Advisor (
    AdvisorID INT PRIMARY KEY,
    AdvisorName VARCHAR(100) NOT NULL
);

CREATE TABLE Application (
    ApplicationID INT PRIMARY KEY,
    TermApplyingFor VARCHAR(20) NOT NULL,
    AdmissionDecision VARCHAR(20),
    UserID INT,
    ProgramID INT,
    AdvisorID INT,

    CONSTRAINT fk_applicant
        FOREIGN KEY (UserID)
        REFERENCES Applicant(UserID),

    CONSTRAINT fk_program
        FOREIGN KEY (ProgramID)
        REFERENCES Program(ProgramID),

    CONSTRAINT fk_advisor
        FOREIGN KEY (AdvisorID)
        REFERENCES Advisor(AdvisorID)
);