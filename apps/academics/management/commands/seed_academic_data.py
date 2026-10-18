import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from apps.academics.models import University, Program, Branch, Semester, Subject, SyllabusUnit
from apps.papers.models import AcademicPaper
from apps.reviews.models import PaperContribution, AuditLog
from apps.syllabus.models import SyllabusDocument
from apps.accounts.models import StudentProfile

User = get_user_model()

MINIMAL_SAMPLE_PDF = (
    b"%PDF-1.4\n"
    b"% Pariksha Sample Academic Test Paper\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"0000000010 00000 n \n"
    b"0000000060 00000 n \n"
    b"0000000117 00000 n \n"
    b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
    b"startxref\n190\n%%EOF\n"
)

class Command(BaseCommand):
    help = "Seed database with sample RGPV academic catalog and initial test users."

    def handle(self, *args, **options):
        self.stdout.write("Starting Pariksha academic catalog seeding...")

        # 1. Create Default Users
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@pariksha.edu",
                "first_name": "System",
                "last_name": "Administrator",
                "role": User.ROLE_ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("pariksha123")
        admin_user.save()

        reviewer_user, _ = User.objects.get_or_create(
            username="reviewer1",
            defaults={
                "email": "reviewer@pariksha.edu",
                "first_name": "Rajesh",
                "last_name": "Sharma",
                "role": User.ROLE_REVIEWER,
                "is_staff": True,
            },
        )
        reviewer_user.set_password("pariksha123")
        reviewer_user.save()

        student_user, _ = User.objects.get_or_create(
            username="student1",
            defaults={
                "email": "student1@pariksha.edu",
                "first_name": "Aarav",
                "last_name": "Patel",
                "role": User.ROLE_STUDENT,
            },
        )
        student_user.set_password("pariksha123")
        student_user.save()

        self.stdout.write(self.style.SUCCESS("  [OK] Sample users created (admin, reviewer1, student1 / pass: pariksha123)"))

        # 2. Create University
        rgpv, _ = University.objects.get_or_create(
            code="RGPV",
            defaults={
                "name": "Rajiv Gandhi Proudyogiki Vishwavidyalaya",
                "short_name": "RGPV Bhopal",
                "location": "Bhopal, Madhya Pradesh",
                "website": "https://www.rgpv.ac.in",
                "is_active": True,
            },
        )

        # 3. Create Program
        btech, _ = Program.objects.get_or_create(
            university=rgpv,
            code="B.Tech",
            defaults={
                "name": "Bachelor of Technology",
                "total_semesters": 8,
                "is_active": True,
            },
        )

        # 4. Create Semesters 1 to 8
        semesters = {}
        sem_titles = [
            "Semester I (1st Sem)", "Semester II (2nd Sem)",
            "Semester III (3rd Sem)", "Semester IV (4th Sem)",
            "Semester V (5th Sem)", "Semester VI (6th Sem)",
            "Semester VII (7th Sem)", "Semester VIII (8th Sem)",
        ]
        for num, title in enumerate(sem_titles, start=1):
            sem, _ = Semester.objects.get_or_create(
                program=btech,
                number=num,
                defaults={"title": title},
            )
            semesters[num] = sem

        # 5. Create Branches
        branch_data = [
            ("CSE", "Computer Science & Engineering"),
            ("IT", "Information Technology"),
            ("EC", "Electronics & Communication Engineering"),
            ("ME", "Mechanical Engineering"),
            ("CE", "Civil Engineering"),
        ]
        branches = {}
        for code, name in branch_data:
            br, _ = Branch.objects.get_or_create(
                program=btech,
                code=code,
                defaults={"name": name, "is_active": True},
            )
            branches[code] = br

        # Set student1 profile defaults
        student_profile, _ = StudentProfile.objects.get_or_create(user=student_user)
        student_profile.university = rgpv
        student_profile.program = btech
        student_profile.branch = branches["CSE"]
        student_profile.semester = semesters[5]
        student_profile.enrollment_number = "0101CS211045"
        student_profile.expected_graduation_year = 2026
        student_profile.save()

        # 6. Create Subjects across all branches and semesters
        cse = branches["CSE"]
        common_first_year_subjects = [
            # Semester 1
            (1, "BT-101", "Engineering Chemistry", 4),
            (1, "BT-102", "Mathematics-I", 4),
            (1, "BT-103", "English for Communication", 3),
            (1, "BT-104", "Basic Electrical & Electronics Engineering", 4),
            (1, "BT-105", "Engineering Graphics", 3),
            # Semester 2
            (2, "BT-201", "Engineering Physics", 4),
            (2, "BT-202", "Mathematics-II", 4),
            (2, "BT-203", "Basic Mechanical Engineering", 3),
            (2, "BT-204", "Basic Civil Engineering & Mechanics", 3),
            (2, "BT-205", "Basic Computer Engineering", 3),
        ]

        subjects = {}
        # Seed 1st year subjects across all engineering branches
        for br_code, branch_obj in branches.items():
            for sem_num, code, name, credits_val in common_first_year_subjects:
                subj, _ = Subject.objects.get_or_create(
                    branch=branch_obj,
                    semester=semesters[sem_num],
                    code=code,
                    defaults={"name": name, "credits": credits_val, "is_active": True},
                )
                if br_code == "CSE":
                    subjects[code] = subj

        # Branch-specific subjects for higher semesters (3 to 8)
        branch_higher_subjects = {
            "CSE": [
                # 3rd sem
                (3, "CS-301", "Discrete Structures", 4),
                (3, "CS-302", "Data Structures & Algorithms", 4),
                (3, "CS-303", "Object Oriented Programming & Methodology", 3),
                # 4th sem
                (4, "CS-401", "Analysis & Design of Algorithms", 4),
                (4, "CS-402", "Computer Organization & Architecture", 4),
                (4, "CS-403", "Theory of Computation", 4),
                # 5th sem
                (5, "CS-501", "Data Communication", 4),
                (5, "CS-502", "Operating Systems", 4),
                (5, "CS-503", "Database Management Systems", 4),
                # 6th sem
                (6, "CS-601", "Software Engineering & Project Management", 4),
                (6, "CS-602", "Computer Networks", 4),
                (6, "CS-603", "Compiler Design", 4),
                # 7th sem
                (7, "CS-701", "Artificial Intelligence & Machine Learning", 4),
                (7, "CS-702", "Information Storage & Management", 4),
                # 8th sem
                (8, "CS-801", "Cloud Computing", 4),
                (8, "CS-802", "Cyber Security", 4),
            ],
            "IT": [
                (3, "IT-301", "Discrete Structures", 4),
                (3, "IT-302", "Data Structures", 4),
                (3, "IT-303", "Object Oriented Programming & Java", 3),
                (4, "IT-401", "Analysis & Design of Algorithms", 4),
                (4, "IT-402", "Computer Organization", 4),
                (4, "IT-403", "Operating Systems", 4),
                (5, "IT-501", "Information Theory & Coding", 4),
                (5, "IT-502", "Operating Systems & System Software", 4),
                (5, "IT-503", "Database Management Systems", 4),
                (6, "IT-601", "Web Engineering", 4),
                (6, "IT-602", "Network Management & Information Security", 4),
                (7, "IT-701", "Data Science & Big Data", 4),
                (7, "IT-702", "Cloud Computing Architecture", 4),
                (8, "IT-801", "Mobile Application Development", 4),
                (8, "IT-802", "Information Storage & Management", 4),
            ],
            "EC": [
                (3, "EC-301", "Signals & Systems", 4),
                (3, "EC-302", "Electronic Devices & Circuits", 4),
                (3, "EC-303", "Digital Circuit Design", 4),
                (4, "EC-401", "Analog Circuits", 4),
                (4, "EC-402", "Communication Systems", 4),
                (4, "EC-403", "Control Systems", 4),
                (5, "EC-501", "Electromagnetic Waves & Radiation", 4),
                (5, "EC-502", "Digital Signal Processing", 4),
                (6, "EC-601", "VLSI Design", 4),
                (6, "EC-602", "Microwave Engineering", 4),
                (7, "EC-701", "Wireless & Mobile Communication", 4),
                (7, "EC-702", "Embedded Systems", 4),
                (8, "EC-801", "Antenna & Wave Propagation", 4),
                (8, "EC-802", "Radar & Navigational Aids", 4),
            ],
            "ME": [
                (3, "ME-301", "Thermodynamics", 4),
                (3, "ME-302", "Mechanics of Materials", 4),
                (3, "ME-303", "Manufacturing Processes", 4),
                (4, "ME-401", "Fluid Mechanics", 4),
                (4, "ME-402", "Theory of Machines", 4),
                (5, "ME-501", "Heat & Mass Transfer", 4),
                (5, "ME-502", "Turbo Machinery", 4),
                (6, "ME-601", "Thermal Engineering & Power Plants", 4),
                (6, "ME-602", "CAD/CAM/CIM", 4),
                (7, "ME-701", "Automobile Engineering", 4),
                (7, "ME-702", "Refrigeration & Air Conditioning", 4),
                (8, "ME-801", "Robotics & Mechatronics", 4),
                (8, "ME-802", "Total Quality Management", 4),
            ],
            "CE": [
                (3, "CE-301", "Building Materials & Construction", 4),
                (3, "CE-302", "Strength of Materials", 4),
                (3, "CE-303", "Surveying", 4),
                (4, "CE-401", "Fluid Mechanics-I", 4),
                (4, "CE-402", "Structural Analysis-I", 4),
                (5, "CE-501", "Structural Analysis-II", 4),
                (5, "CE-502", "Fluid Mechanics-II", 4),
                (6, "CE-601", "Design of Steel Structures", 4),
                (6, "CE-602", "Geotechnical Engineering", 4),
                (7, "CE-701", "Design of RCC Structures", 4),
                (7, "CE-702", "Transportation Engineering", 4),
                (8, "CE-801", "Construction Planning & Management", 4),
                (8, "CE-802", "Advanced Structural Design", 4),
            ],
        }

        for br_code, sub_list in branch_higher_subjects.items():
            branch_obj = branches[br_code]
            for sem_num, code, name, credits_val in sub_list:
                subj, _ = Subject.objects.get_or_create(
                    branch=branch_obj,
                    semester=semesters[sem_num],
                    code=code,
                    defaults={"name": name, "credits": credits_val, "is_active": True},
                )
                if br_code == "CSE":
                    subjects[code] = subj

        self.stdout.write(self.style.SUCCESS("  [OK] Universities, branches, semesters, and subjects configured."))

        # 7. Add Syllabus Units for Core Subjects
        # CS-502 (Operating Systems)
        os_subj = subjects["CS-502"]
        os_units = [
            (1, "Unit 1: Introduction to Operating Systems", "OS concepts, system calls, system structures, kernel architectures (monolithic vs microkernel), boot sequence."),
            (2, "Unit 2: Process Management & CPU Scheduling", "Process states, PCB, Context Switching, Inter-Process Communication, Threads, Scheduling Algorithms (FCFS, SJF, Round Robin, Multilevel Feedback)."),
            (3, "Unit 3: Process Synchronization & Deadlocks", "Race conditions, Critical Section problem, Peterson's algorithm, Semaphores, Monitors, Classical synchronization problems, Deadlock prevention, avoidance (Banker's Algorithm), and detection."),
            (4, "Unit 4: Memory Management & Virtual Memory", "Contiguous allocation, Paging, Segmentation, Page replacement policies (FIFO, LRU, Optimal), Thrashing, Working Set Model."),
            (5, "Unit 5: Storage Management & File Systems", "Disk scheduling algorithms (FCFS, SSTF, SCAN, C-SCAN), File allocation methods, Directory structures, Free space management, Protection."),
        ]
        for u_num, u_title, u_desc in os_units:
            SyllabusUnit.objects.get_or_create(
                subject=os_subj,
                unit_number=u_num,
                defaults={"title": u_title, "description": u_desc},
            )

        # CS-503 (Database Management Systems)
        dbms_subj = subjects["CS-503"]
        dbms_units = [
            (1, "Unit 1: Introduction & ER Modeling", "DBMS architecture, data independence, Entity-Relationship model, Extended ER features."),
            (2, "Unit 2: Relational Model & Relational Algebra", "Relational constraints, Relational algebra operators, Tuple and Domain relational calculus."),
            (3, "Unit 3: SQL & Relational Database Design", "DDL, DML, Complex queries, Functional Dependencies, Normalization (1NF, 2NF, 3NF, BCNF, 4NF)."),
            (4, "Unit 4: Transaction Processing & Concurrency Control", "ACID properties, Serializability, Two-Phase Locking (2PL), Timestamp ordering, Deadlock handling."),
            (5, "Unit 5: Storage Structures & Query Processing", "Indexing (B-Tree, B+ Tree), Hashing techniques, Query evaluation and optimization."),
        ]
        for u_num, u_title, u_desc in dbms_units:
            SyllabusUnit.objects.get_or_create(
                subject=dbms_subj,
                unit_number=u_num,
                defaults={"title": u_title, "description": u_desc},
            )

        # BT-205 (Basic Computer Engineering - 2nd Semester)
        bce_subj = subjects["BT-205"]
        bce_units = [
            (1, "Unit 1: Computer Fundamentals & Hardware Architecture", "Computer systems organization, CPU, memory hierarchy, primary vs secondary storage, I/O devices, operating system overview and functions."),
            (2, "Unit 2: Programming Fundamentals & Logic", "Algorithms, flowcharting, pseudocode, introduction to programming languages, compilation vs interpretation."),
            (3, "Unit 3: Object-Oriented Programming with C++", "Classes, objects, data encapsulation, inheritance, polymorphism, function overloading, constructors and destructors."),
            (4, "Unit 4: Data Structures & File Concepts", "Arrays, stacks, queues, linked lists overview, basic searching and sorting methods, file organization and storage."),
            (5, "Unit 5: Computer Networks & Internet Basics", "OSI model, TCP/IP reference model, LAN/WAN topologies, network security, firewalls, and cyber ethics."),
        ]
        for u_num, u_title, u_desc in bce_units:
            SyllabusUnit.objects.get_or_create(
                subject=bce_subj,
                unit_number=u_num,
                defaults={"title": u_title, "description": u_desc},
            )

        # BT-201 (Engineering Physics - 2nd Semester)
        phy_subj = subjects["BT-201"]
        phy_units = [
            (1, "Unit 1: Wave Optics & Interference", "Interference of light, Young's double slit experiment, Newton's rings, diffraction (Fresnel and Fraunhofer), resolving power."),
            (2, "Unit 2: Lasers & Fiber Optics", "Stimulated emission, population inversion, Ruby laser, He-Ne laser, optical fiber types, numerical aperture, attenuation."),
            (3, "Unit 3: Quantum Mechanics", "De Broglie hypothesis, Heisenberg uncertainty principle, Schrodinger wave equations (time-dependent and independent), particle in a box."),
            (4, "Unit 4: Semiconductor Physics & Superconductivity", "Intrinsic and extrinsic semiconductors, Fermi energy level, Hall effect, Meissner effect, Type I and Type II superconductors."),
            (5, "Unit 5: Nanotechnology & Acoustics", "Nanomaterials synthesis and characterization, carbon nanotubes, acoustics of buildings, Sabine's formula, ultrasonic production."),
        ]
        for u_num, u_title, u_desc in phy_units:
            SyllabusUnit.objects.get_or_create(
                subject=phy_subj,
                unit_number=u_num,
                defaults={"title": u_title, "description": u_desc},
            )

        self.stdout.write(self.style.SUCCESS("  [OK] Official Syllabus units seeded for core subjects."))

        # 8. Seed Sample Verified Academic Papers (PYQs)
        sample_papers_spec = [
            (subjects["BT-205"], 2023, "Nov-Dec", "BT-205 Basic Computer Engineering (Nov-Dec 2023)"),
            (subjects["BT-205"], 2023, "May-June", "BT-205 Basic Computer Engineering (May-June 2023)"),
            (subjects["BT-201"], 2023, "Nov-Dec", "BT-201 Engineering Physics (Nov-Dec 2023)"),
            (subjects["BT-102"], 2023, "Nov-Dec", "BT-102 Mathematics-I (Nov-Dec 2023)"),
            (subjects["CS-502"], 2023, "Nov-Dec", "CS-502 Operating Systems (Nov-Dec 2023)"),
            (subjects["CS-502"], 2023, "May-June", "CS-502 Operating Systems (May-June 2023)"),
            (subjects["CS-502"], 2022, "Nov-Dec", "CS-502 Operating Systems (Nov-Dec 2022)"),
            (subjects["CS-503"], 2023, "Nov-Dec", "CS-503 Database Management Systems (Nov-Dec 2023)"),
            (subjects["CS-503"], 2023, "May-June", "CS-503 Database Management Systems (May-June 2023)"),
            (subjects["CS-501"], 2023, "Nov-Dec", "CS-501 Data Communication (Nov-Dec 2023)"),
            (subjects["CS-401"], 2023, "May-June", "CS-401 Analysis & Design of Algorithms (May-June 2023)"),
            (subjects["CS-402"], 2023, "May-June", "CS-402 Computer Organization & Architecture (May-June 2023)"),
            (subjects["CS-601"], 2023, "May-June", "CS-601 Software Engineering (May-June 2023)"),
            (subjects["CS-602"], 2023, "May-June", "CS-602 Computer Networks (May-June 2023)"),
        ]

        for subj, year, sess, title in sample_papers_spec:
            paper, created = AcademicPaper.objects.get_or_create(
                university=rgpv,
                program=btech,
                branch=subj.branch,
                semester=subj.semester,
                subject=subj,
                exam_year=year,
                exam_session=sess,
                defaults={
                    "paper_title": title,
                    "paper_code": f"QP-{subj.code}-{year}",
                    "file_size": len(MINIMAL_SAMPLE_PDF),
                    "file_type": "application/pdf",
                    "is_verified": True,
                    "contributor": student_user,
                    "verified_by": reviewer_user,
                    "downloads_count": 14,
                },
            )
            if created or not paper.file:
                paper.file.save(f"{subj.code}_{sess}_{year}.pdf", ContentFile(MINIMAL_SAMPLE_PDF), save=True)

        self.stdout.write(self.style.SUCCESS("  [OK] Verified PYQ question papers cataloged with sample PDF files."))

        # 9. Seed Sample Pending Contribution for Reviewer Testing
        pending_contrib, created = PaperContribution.objects.get_or_create(
            university=rgpv,
            program=btech,
            branch=cse,
            semester=semesters[7],
            subject=subjects["CS-701"],
            exam_year=2023,
            exam_session="Nov-Dec",
            defaults={
                "contributor": student_user,
                "paper_title": "CS-701 AI & ML Nov-Dec 2023",
                "original_filename": "CS701_AI_ML_Dec2023_scanned.pdf",
                "file_size": len(MINIMAL_SAMPLE_PDF),
                "file_type": "application/pdf",
                "notes": "Original mid-sem and end-sem question paper copy, all 8 questions legible.",
                "status": PaperContribution.STATUS_PENDING,
            },
        )
        if created or not pending_contrib.file:
            pending_contrib.file.save("CS701_pending.pdf", ContentFile(MINIMAL_SAMPLE_PDF), save=True)

        # 10. Seed Official Published Syllabus Document
        syllabus_doc, created = SyllabusDocument.objects.get_or_create(
            university=rgpv,
            program=btech,
            branch=cse,
            semester=semesters[5],
            subject=os_subj,
            academic_year="2023-2024",
            defaults={
                "version": "CBGS-2023.1",
                "title": "RGPV B.Tech V-Sem CSE Scheme & Syllabus - CS502 Operating Systems",
                "file_size": len(MINIMAL_SAMPLE_PDF),
                "is_published": True,
                "uploaded_by": admin_user,
                "notes": "Official RGPV Scheme with AICTE model curriculum alignment.",
            },
        )
        if created or not syllabus_doc.file:
            syllabus_doc.file.save("CS502_Official_Syllabus.pdf", ContentFile(MINIMAL_SAMPLE_PDF), save=True)

        self.stdout.write(self.style.SUCCESS("  [OK] Pending contribution and official syllabus document seeded."))
        self.stdout.write(self.style.SUCCESS("Pariksha academic data seeding complete!"))
