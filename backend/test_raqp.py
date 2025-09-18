import pytest
from raqp import RAQP

def test_select():
    input_text = """
Employees (EID, Name, Age) = {
    E1, John, 32
    E2, Alice, 28
    E3, Bob, 29
}

Query: select Age > 30 (Employees)
    """
    expected = """
Employees = {EID, Name, Age
  "E1", "John", 32
}
    """
    result = RAQP.process(input_text)
    assert result.text.strip() == expected.strip()

def test_project():
    input_text = """
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
  E3, Bob, 29
}

Query: project Name, Age (Employees)
    """
    expected = """
Employees = {Name, Age
  "John", 32
  "Alice", 28
  "Bob", 29
}
"""
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_join():
    input_text = """
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
  E3, Bob, 29
}

Departments (DID, DName, EID) = {
  D1, HR, E2
  D2, IT, E1
  D3, Finance, E3
}

Query: Employees join Employees.EID = Departments.EID Departments
    """
    expected = """
Employees = {EID, Name, Age, DID, DName
  "E1", "John", 32, "D2", "IT"
  "E2", "Alice", 28, "D1", "HR"
  "E3", "Bob", 29, "D3", "Finance"
}
"""
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_union():
    input_text = """
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
  E3, Bob, 29
  E4, Carol, 35
}

Managers (MID, Name, Age) = {
  M1, Alice, 28
  M2, David, 40
}

Query: (project Name (select Age > 30 (Employees))) union (project Name (Managers))
    """
    expected = """
Employees = {Name
  "John"
  "Carol"
  "Alice"
  "David"
}
"""
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_intersect():
    input_text = """
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
  E3, Bob, 29
  E4, Carol, 35
}

Managers (MID, Name, Age) = {
  M1, Alice, 28
  M2, David, 40
  M3, Carol, 35
}

Query: (project Name (Employees)) intersect (project Name (Managers))
    """
    expected = """
Employees = {Name
  "Alice"
  "Carol"
}
"""
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_diff():
    input_text = """
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
  E3, Bob, 29
  E4, Carol, 35
}

Contractors (CID, Name) = {
  C1, Bob
  C2, Carol
  C3, Eve
}

Query: (project Name (Employees)) - (project Name (Contractors))
    """
    expected = """
Employees = {Name
  "John"
  "Alice"
}
"""
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_nested_1():
    input_text = """
Student (ID, Name, Age, Major) = {
  1, Alice, 20, Computer Science
  2, Bob, 22, Physics
  3, Charlie, 21, Mathematics
}

Courses (CourseID, CourseName, Professor) = {
  C101, Databases, Smith
  C102, Physics, Doe
  C103, Calculus, White
}

Enrollment (StudentID, CourseID) = {
  1, C101
  2, C102
  3, C103
}

Query: project Name ((Student join Student.ID = Enrollment.StudentID Enrollment) join Student.CourseID = Courses.CourseID Courses) - project Name (select Professor = Smith ((Student join Student.ID = Enrollment.StudentID Enrollment) join Student.CourseID = Courses.CourseID Courses))
"""
    expected = """
Student = {Name
  "Bob"
  "Charlie"
}
"""
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_nested_2():
    input_text = """
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
  E3, Bob, 29
  E4, Carol, 35
  E5, Eve, 41
}

Departments (DID, DName, EID) = {
  D1, HR, E2
  D2, IT, E1
  D3, Finance, E3
  D4, Sales, E4
}

Managers (MID, Name, Age) = {
  M1, Alice, 28
  M2, David, 40
  M3, Eve, 41
}

Query:
(
   project Name (
       select Age > 30 (Employees join Employees.EID = Departments.EID Departments)
   )
)
union
(
   (project Name (Managers)) intersect (project Name (Employees))
)
-
(
   project Name (select Age < 30 (Employees))
)
"""
    expected = """
Employees = {Name
  "John"
  "Carol"
  "Eve"
}
"""
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_no_result():
    input_text = """
Employees (EID, Name, Age) = {
    E1, John, 32
    E2, Alice, 28
    E3, Bob, 29
}

Query: select Age > 100 (Employees)
"""
    expected = "No result."
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_empty_relations():
    input_text = """
Employees (EID, Name, Age) = {
}

Query: select Age > 30 (Employees)
"""
    expected = "No result."
    result = RAQP.process(input_text)
    print(result.text.strip())
    assert result.text.strip() == expected.strip()

def test_invalid_query():
    input_text = """
Employees (EID, Name, Age) = {
    E1, John, 32
    E2, Alice, 28
    E3, Bob, 29
}

Query: invalid_operation (Employees)
"""
    with pytest.raises(Exception):
        RAQP.process(input_text)