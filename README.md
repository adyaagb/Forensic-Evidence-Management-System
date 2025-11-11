# Forensic Evidence Management System (FEMS)

##  Project Overview

[cite_start]This project implements a secure, web-based *Forensic Evidence Management System (FEMS)* designed to digitize, store, organize, and analyze data related to criminal cases and forensic investigations[cite: 695, 709].

[cite_start]The system serves as a centralized digital platform for law enforcement and forensic teams to efficiently manage and track cases, suspects, reports, evidence, and laboratory data, addressing issues like data duplication, inconsistency, and limited traceability often found in traditional, manual systems[cite: 695, 704, 706].

##  Key Features

The platform provides role-based access and advanced database features to ensure data security and quick analytics:

### Application Features (Frontend/Backend)
* [cite_start]*Secure Authentication:* Uses Flask-Login for session management and werkzeug.security to hash and verify user passwords[cite: 715, 717].
* [cite_start]*Role-Based Access:* Supports two roles: *Admin* (full CRUD access and user management) and *Read-only* (view only)[cite: 715, 902].
* [cite_start]*Data Management (CRUD):* Admins can Create, Read, Update, and Delete records across all core tables (Cases, Suspects, Evidence, Reports, etc.) dynamically[cite: 715, 902].
* [cite_start]*Analytics Section:* Displays visual summary statistics and results from advanced SQL queries (aggregate, joins, nested queries) on the Dashboard[cite: 715, 902].
* [cite_start]*Tools Page:* Allows direct execution of SQL Stored Procedures like Add_Case_With_Report() and Get_Suspect_Aliases() via the UI[cite: 715, 902].
* [cite_start]*Triggers Log View:* Provides a real-time "Evidence Log" to show trigger events[cite: 902].

### Database Features (SQL)
* [cite_start]*Stored Procedure:* Get_Suspect_Aliases(): Retrieves the main name and all associated aliases for every suspect [cite: 861, 863-867].
* *Functions:*
    * [cite_start]get_age(dob DATE): Calculates the age of a suspect based on their Date of Birth (DOB)[cite: 871, 874].
    * [cite_start]total_evidence(caseId INT): Returns the total count of evidence items linked to a specific case [cite: 878, 883-886].
* [cite_start]*Trigger:* trg_after_evidence_insert: An AFTER INSERT trigger that automatically logs a new entry into an Evidence_Log table whenever a new piece of evidence is added [cite: 891-897].

## Technology Stack

[cite_start]The system utilizes a Python-based backend connected to a MySQL relational database[cite: 697, 698].

| Category | Tool / Technology | Purpose / Functionality |
| :--- | :--- | :--- |
| *Backend Framework* | *Flask (Python)* | [cite_start]Web framework for routing, logic, and authentication[cite: 697, 717]. |
| *Database* | *MySQL* | [cite_start]Relational database for storing forensic data and relationships[cite: 698, 717]. |
| *Database Connector* | mysql-connector-python | [cite_start]Used for executing SQL queries and stored procedures with connection pooling[cite: 717]. |
| *Authentication* | *Flask-Login, Werkzeug* | [cite_start]Handles session management, user authentication, and password hashing/security[cite: 717]. |
| *Frontend Design* | *HTML5, CSS3, Bootstrap 5* | [cite_start]Creates a responsive and modern UI for the dashboard, tables, and forms[cite: 699, 717]. |

##  Database Schema (Relational Mapping)

The core tables and their relationships are designed to support the complete forensic investigation lifecycle:

| Table Name | Description | Key Relationships (via Foreign Keys) |
| :--- | :--- | :--- |
| Case_ | Stores primary case details (Title, Description). | Related to Report, Suspect, Trial, Witnessed |
| Evidence | Stores details of collected evidence. | Linked to Investigator, Lab, Trial, Test_Result |
| Evidence_Item | Stores itemized details (Quantity, Description) of a piece of Evidence. | Linked to Evidence |
| Suspect | Stores suspect information (Name, DOB, Address). | Linked to Case_, Suspect_Alias, Trial |
| Lab | Details of forensic laboratories. | Linked to Evidence, Test_Result |
| Investigator | Details of the personnel handling the investigation. | Linked to Evidence |
| Trial | Stores the many-to-many relationship between a case, court, suspect, and evidence. | Linked to Case_, Court, Suspect, Evidence |
| users | Stores system users for Flask authentication (username, password_hash, role). | None |

##  Installation and Setup

### Prerequisites

* Python 3.x
* MySQL Server
* Required Python packages (Flask, mysql-connector-python, Flask-Login, etc. - typically listed in a requirements.txt file).

### Steps

1.  *Clone the Repository:*
    bash
    git clone [https://github.com/](https://github.com/)<GITHUB_USERNAME>/Forensic-Evidence-Management-System
    cd Forensic-Evidence-Management-System
    
2.  *Database Setup:*
    * Create a database named forensic_db (or similar).
    * Execute the DDL statements from the provided SQL file (or report section 6) to create all tables.
    * Execute the DML statements (INSERT) to populate initial data and users.
3.  *Configure Environment:*
    * Set up a virtual environment and install dependencies.
    * [cite_start]Configure database credentials (username, password, database name) in the application's environment configuration (likely using python-dotenv as mentioned in the report)[cite: 717].
4.  *Run the Flask Application:*
    bash
    # Command may vary, but typically
    python app.py 
    # OR
    flask run
    
5.  Access the application via the browser (default http://127.0.0.1:5000/).

##  Contributors

* *Adyaa GB* (PES2UG23AM006)
* *Adyanth S* (PES2UG23AM007)

## 🔗 Repository Link

* [cite_start]*GitHub Repository:* adyaagb/Forensic-Evidence-Management-System [cite: 910]
