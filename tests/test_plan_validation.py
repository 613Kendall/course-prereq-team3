import pytest
import networkx as nx

import planGenerator.plan_validation as plangen
from graph.prereq_graph import build_graph


# ---------------------------------------------------------
# TEST DATA / FIXTURES
# ---------------------------------------------------------

@pytest.fixture
def sample_data():
    return {
        "courses": [
            {
                "course_id": 100,
                "course_title": "Intro Course",
                "course_identifier": "TEST.100",
                "is_repeatable": False
            },
            {
                "course_id": 200,
                "course_title": "Prerequisite A",
                "course_identifier": "TEST.200",
                "is_repeatable": False
            },
            {
                "course_id": 300,
                "course_title": "Prerequisite B",
                "course_identifier": "TEST.300",
                "is_repeatable": False
            },
            {
                "course_id": 400,
                "course_title": "Repeatable Course",
                "course_identifier": "TEST.400",
                "is_repeatable": True
            }
        ],

        "prerequisite_groups": [
            {
                "prerequisite_group_id": 1,
                "course_id": 100,
                "group_operator": "AND",
                "parent_group_id": None
            }
        ],

        "prerequisites": [
            {
                "prerequisite_id": 1,
                "prerequisite_group_id": 1,
                "prerequisite_course_id": 200,
                "negative_prerequisite": False,
                "min_grade": "C",
                "concurrent_allowed": False
            }
        ]
    }


@pytest.fixture
def graph(sample_data):
    return build_graph(sample_data)


# ---------------------------------------------------------
# BUILD GRAPH TESTS
# ---------------------------------------------------------

def test_build_graph_returns_digraph(graph):
    assert isinstance(graph, nx.DiGraph)


def test_course_node_attributes(graph):
    assert graph.nodes[100]["node_type"] == "course"
    assert graph.nodes[100]["course_identifier"] == "TEST.100"
    assert graph.nodes[100]["is_repeatable"] is False

    assert graph.nodes[400]["is_repeatable"] is True


def test_group_node_attributes(graph):
    assert "group_1" in graph
    assert graph.nodes["group_1"]["node_type"] == "group"
    assert graph.nodes["group_1"]["operator"] == "AND"


def test_group_connected_to_target_course(graph):
    assert graph.has_edge("group_1", 100)


def test_prerequisite_connected_to_group(graph):
    assert graph.has_edge(200, "group_1")

    edge_data = graph.get_edge_data(200, "group_1")

    assert edge_data["min_grade"] == "C"
    assert edge_data["concurrent_allowed"] is False
    assert edge_data["negative_prerequisite"] is False


# ---------------------------------------------------------
# COMPLETED COURSE TESTS
# ---------------------------------------------------------

def test_get_completed_courses():
    history = [
        {
            "course_id": 100,
            "status": "completed",
            "grade": "A"
        },
        {
            "course_id": 200,
            "status": "withdrawn",
            "grade": "W"
        },
        {
            "course_id": 300,
            "status": "completed",
            "grade": "B"
        }
    ]

    completed = plangen.get_completed_courses(history)

    assert 100 in completed
    assert 300 in completed
    assert 200 not in completed


def test_get_completed_courses_multiple_attempts():
    history = [
        {
            "course_id": 200,
            "status": "completed",
            "grade": "F"
        },
        {
            "course_id": 200,
            "status": "completed",
            "grade": "B"
        }
    ]

    completed = plangen.get_completed_courses(history)

    assert len(completed[200]) == 2


# ---------------------------------------------------------
# MINIMUM GRADE TESTS
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "student_grade,min_grade,expected",
    [
        ("A", "C", True),
        ("B", "C", True),
        ("C", "C", True),
        ("D", "C", False),
        ("F", "C", False),
        ("W", "C", False),
        ("I", "C", False),
        (None, "C", False),

        ("A", None, True),
        ("D", None, True),
        ("F", None, False),

        ("P", None, True),
        ("P", "C", False),
    ]
)
def test_min_grade_satisfaction(
    student_grade,
    min_grade,
    expected
):
    assert (
        plangen.min_grade_satisfaction(
            student_grade,
            min_grade
        )
        == expected
    )


# ---------------------------------------------------------
# OFFERING STATUS TESTS
# ---------------------------------------------------------

def test_course_not_offered(monkeypatch):
    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: []
    )

    assert (
        plangen.course_offer_status(100, 1)
        == "not_offered"
    )


def test_course_open(monkeypatch):
    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Open"}
        ]
    )

    assert plangen.course_offer_status(100, 1) == "open"


def test_course_waitlist(monkeypatch):
    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Waitlist Only"}
        ]
    )

    assert (
        plangen.course_offer_status(100, 1)
        == "waitlist"
    )


def test_course_closed(monkeypatch):
    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Closed"}
        ]
    )

    assert plangen.course_offer_status(100, 1) == "closed"


def test_open_section_overrides_closed(monkeypatch):
    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Closed"},
            {"status": "Open"}
        ]
    )

    assert plangen.course_offer_status(100, 1) == "open"


# ---------------------------------------------------------
# EXTERNAL CREDIT TESTS
# ---------------------------------------------------------

def test_get_external_courses():
    external_data = [
        {
            "equivalent_course_id": 200
        },
        {
            "equivalent_course_id": 300
        },
        {
            "equivalent_course_id": None
        }
    ]

    courses = plangen.get_external_courses(
        external_data
    )

    assert courses == {200, 300}


def test_external_credit_satisfies_prerequisite(graph):
    completed_courses = {}

    external_courses = {200}

    result = plangen.course_prereq_satisfaction(
        graph,
        200,
        "group_1",
        completed_courses,
        external_courses
    )

    assert result is True


# ---------------------------------------------------------
# PREREQUISITE SATISFACTION TESTS
# ---------------------------------------------------------

def test_prerequisite_satisfied_by_grade(graph):
    completed = {
        200: [
            {
                "course_id": 200,
                "status": "completed",
                "grade": "B"
            }
        ]
    }

    assert plangen.course_prereq_satisfaction(
        graph,
        200,
        "group_1",
        completed,
        set()
    ) is True


def test_prerequisite_fails_min_grade(graph):
    completed = {
        200: [
            {
                "course_id": 200,
                "status": "completed",
                "grade": "D"
            }
        ]
    }

    assert plangen.course_prereq_satisfaction(
        graph,
        200,
        "group_1",
        completed,
        set()
    ) is False


def test_multiple_attempts_can_satisfy_prerequisite(graph):
    completed = {
        200: [
            {
                "course_id": 200,
                "status": "completed",
                "grade": "F"
            },
            {
                "course_id": 200,
                "status": "completed",
                "grade": "B"
            }
        ]
    }

    assert plangen.course_prereq_satisfaction(
        graph,
        200,
        "group_1",
        completed,
        set()
    ) is True


# ---------------------------------------------------------
# NEGATIVE PREREQUISITE TESTS
# ---------------------------------------------------------

def test_negative_prerequisite_not_taken():
    G = nx.DiGraph()

    G.add_node(
        200,
        node_type="course"
    )

    G.add_node(
        "group_1",
        node_type="group",
        operator="AND"
    )

    G.add_edge(
        200,
        "group_1",
        min_grade=None,
        concurrent_allowed=False,
        negative_prerequisite=True
    )

    assert plangen.course_prereq_satisfaction(
        G,
        200,
        "group_1",
        {},
        set()
    ) is True


def test_negative_prerequisite_completed():
    G = nx.DiGraph()

    G.add_node(
        200,
        node_type="course"
    )

    G.add_node(
        "group_1",
        node_type="group",
        operator="AND"
    )

    G.add_edge(
        200,
        "group_1",
        min_grade=None,
        concurrent_allowed=False,
        negative_prerequisite=True
    )

    completed = {
        200: [
            {
                "grade": "A",
                "status": "completed"
            }
        ]
    }

    assert plangen.course_prereq_satisfaction(
        G,
        200,
        "group_1",
        completed,
        set()
    ) is False


# ---------------------------------------------------------
# GROUP LOGIC TESTS
# ---------------------------------------------------------

def test_and_group():
    G = nx.DiGraph()

    G.add_node(
        "group_1",
        node_type="group",
        operator="AND"
    )

    for course_id in [200, 300]:
        G.add_node(
            course_id,
            node_type="course"
        )

        G.add_edge(
            course_id,
            "group_1",
            min_grade=None,
            concurrent_allowed=False,
            negative_prerequisite=False
        )

    completed = {
        200: [
            {
                "grade": "A",
                "status": "completed"
            }
        ],
        300: [
            {
                "grade": "B",
                "status": "completed"
            }
        ]
    }

    assert plangen.evaluate_group(
        G,
        "group_1",
        completed,
        set()
    ) is True


def test_and_group_missing_course():
    G = nx.DiGraph()

    G.add_node(
        "group_1",
        node_type="group",
        operator="AND"
    )

    for course_id in [200, 300]:
        G.add_node(
            course_id,
            node_type="course"
        )

        G.add_edge(
            course_id,
            "group_1",
            min_grade=None,
            concurrent_allowed=False,
            negative_prerequisite=False
        )

    completed = {
        200: [
            {
                "grade": "A",
                "status": "completed"
            }
        ]
    }

    assert plangen.evaluate_group(
        G,
        "group_1",
        completed,
        set()
    ) is False


def test_or_group():
    G = nx.DiGraph()

    G.add_node(
        "group_1",
        node_type="group",
        operator="OR"
    )

    for course_id in [200, 300]:
        G.add_node(
            course_id,
            node_type="course"
        )

        G.add_edge(
            course_id,
            "group_1",
            min_grade=None,
            concurrent_allowed=False,
            negative_prerequisite=False
        )

    completed = {
        300: [
            {
                "grade": "A",
                "status": "completed"
            }
        ]
    }

    assert plangen.evaluate_group(
        G,
        "group_1",
        completed,
        set()
    ) is True


# ---------------------------------------------------------
# UNMET PREREQUISITE TESTS
# ---------------------------------------------------------

def test_unmet_and_group():
    G = nx.DiGraph()

    G.add_node(
        "group_1",
        node_type="group",
        operator="AND"
    )

    for course_id in [200, 300]:
        G.add_node(
            course_id,
            node_type="course"
        )

        G.add_edge(
            course_id,
            "group_1",
            min_grade=None,
            concurrent_allowed=False,
            negative_prerequisite=False
        )

    completed = {
        200: [
            {
                "grade": "A",
                "status": "completed"
            }
        ]
    }

    result = plangen.get_unmet_prereqs(
        G,
        "group_1",
        completed,
        set()
    )
    assert result is not None
    assert result["operator"] == "AND"

    assert result["requirements"] == [
        {
            "type": "course",
            "course_id": 300
        }
    ]


def test_unmet_or_group():
    G = nx.DiGraph()

    G.add_node(
        "group_1",
        node_type="group",
        operator="OR"
    )

    for course_id in [200, 300]:
        G.add_node(
            course_id,
            node_type="course"
        )

        G.add_edge(
            course_id,
            "group_1",
            min_grade=None,
            concurrent_allowed=False,
            negative_prerequisite=False
        )

    result = plangen.get_unmet_prereqs(
        G,
        "group_1",
        {},
        set()
    )

    assert result is not None
    assert result["operator"]== "OR"

    missing_ids = {
        requirement["course_id"]
        for requirement in result["requirements"]
    }

    assert missing_ids == {200, 300}


# ---------------------------------------------------------
# COURSE VALIDATION TESTS
# ---------------------------------------------------------

def test_invalid_course(graph):
    result = plangen.course_validation(
        graph,
        student_id=1,
        target_course_id=-999,
        term_id=1
    )

    assert result["eligible"] is False
    assert result["reason"] == "invalid_course"


def test_already_completed_nonrepeatable(
    graph,
    monkeypatch
):
    monkeypatch.setattr(
        plangen,
        "get_user_data",
        lambda student_id: [
            {
                "course_id": 100,
                "status": "completed",
                "grade": "A"
            }
        ]
    )

    monkeypatch.setattr(
        plangen,
        "get_external_credits",
        lambda student_id: []
    )

    result = plangen.course_validation(
        graph,
        1,
        100,
        1
    )

    assert result["eligible"] is False
    assert result["reason"] == "already_completed"


def test_validation_not_offered(
    graph,
    monkeypatch
):
    monkeypatch.setattr(
        plangen,
        "get_user_data",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_external_credits",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: []
    )

    result = plangen.course_validation(
        graph,
        1,
        100,
        1
    )

    assert result["eligible"] is False
    assert result["reason"] == "not_offered"


def test_validation_closed(
    graph,
    monkeypatch
):
    monkeypatch.setattr(
        plangen,
        "get_user_data",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_external_credits",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Closed"}
        ]
    )

    result = plangen.course_validation(
        graph,
        1,
        100,
        1
    )

    assert result["eligible"] is False
    assert result["reason"] == "offering_closed"


def test_validation_waitlist(
    graph,
    monkeypatch
):
    monkeypatch.setattr(
        plangen,
        "get_user_data",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_external_credits",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Waitlist Only"}
        ]
    )

    result = plangen.course_validation(
        graph,
        1,
        100,
        1
    )

    assert result["eligible"] is False
    assert result["reason"] == "waitlist_only"


def test_validation_missing_prerequisite(
    graph,
    monkeypatch
):
    monkeypatch.setattr(
        plangen,
        "get_user_data",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_external_credits",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Open"}
        ]
    )

    result = plangen.course_validation(
        graph,
        1,
        100,
        1
    )

    assert result["eligible"] is False

    assert (
        result["reason"]
        == "prerequisites_not_satisfied"
    )

    assert "unmet_prerequisites" in result


def test_validation_prerequisite_satisfied(
    graph,
    monkeypatch
):
    monkeypatch.setattr(
        plangen,
        "get_user_data",
        lambda student_id: [
            {
                "course_id": 200,
                "status": "completed",
                "grade": "B"
            }
        ]
    )

    monkeypatch.setattr(
        plangen,
        "get_external_credits",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Open"}
        ]
    )

    result = plangen.course_validation(
        graph,
        1,
        100,
        1
    )

    assert result["eligible"] is True

    assert (
        result["reason"]
        == "satisfy_all_prerequisites"
    )


def test_validation_external_credit_satisfies_prereq(
    graph,
    monkeypatch
):
    monkeypatch.setattr(
        plangen,
        "get_user_data",
        lambda student_id: []
    )

    monkeypatch.setattr(
        plangen,
        "get_external_credits",
        lambda student_id: [
            {
                "equivalent_course_id": 200,
                "approval_status": "approved"
            }
        ]
    )

    monkeypatch.setattr(
        plangen,
        "get_course_offerings",
        lambda course_id, term_id: [
            {"status": "Open"}
        ]
    )

    result = plangen.course_validation(
        graph,
        1,
        100,
        1
    )

    assert result["eligible"] is True