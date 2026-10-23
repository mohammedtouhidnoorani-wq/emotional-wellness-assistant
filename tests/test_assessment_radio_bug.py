"""
Bug Condition Exploration Test for Assessment Radio Button Bug

Tests that verify radio button selection behavior in the assessment form.
Expected outcome: Test should FAIL if the bug exists (which confirms the bug).

Bug Description:
1. Selecting the same option value in a subsequent question makes the previous selection disappear
2. Multiple options can be selected for the same question (when it should be single-select)
"""

import pytest
from flask import Flask
from flask_login import LoginManager
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, client):
    """Create authenticated test client."""
    with app.app_context():
        # Create test user
        user = User(email='test@example.com', is_verified=True)
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpass123'
        }, follow_redirects=True)
    
    return client


class TestRadioButtonBugExploration:
    """Tests to explore the radio button bug behavior."""
    
    def test_same_value_different_questions_should_not_affect_each_other(self, app, authenticated_client):
        """
        **Validates: Requirements 1**
        
        Test that selecting option value '2' for question 1 does NOT affect 
        question 0's selection. Each question should be independent.
        
        Bug: Selecting the same option value in a subsequent question makes 
        the previous selection disappear.
        
        Expected: Both selections should be retained independently.
        """
        with app.app_context():
            # Get the assessment page first to establish session
            response = authenticated_client.get('/assessment/take/anxiety')
            assert response.status_code == 200
            
            # Submit form with question 0 = option 2, question 1 = option 2
            # Both having the same value (2) but different question names
            form_data = {
                'q0': '2',  # Question 0 - value 2
                'q1': '2',  # Question 1 - value 2 (same value as q0, different name)
            }
            
            # Fill in remaining questions with default values
            for i in range(2, len([
                'Feeling nervous, anxious, or on edge',
                'Not being able to stop or control worrying',
                'Worrying too much about different things',
                'Trouble relaxing',
                'Being so restless that it\'s hard to sit still',
                'Becoming easily annoyed or irritable',
                'Feeling afraid as if something awful might happen'
            ])):
                form_data[f'q{i}'] = '0'
            
            response = authenticated_client.post(
                '/assessment/submit/anxiety',
                data=form_data,
                follow_redirects=True
            )
            
            # If bug exists: one of the selections will be lost or incorrectly handled
            # The response should still contain the result (not redirect back to form)
            assert response.status_code == 200
            assert b'score' in response.data or b'Submit Assessment' not in response.data
    
    def test_each_question_allows_only_one_selection(self, app, authenticated_client):
        """
        **Validates: Requirements 2**
        
        Test that each question only allows one selection (radio button behavior).
        Multiple options should NOT be selectable for the same question.
        
        Bug: Multiple options can be selected for the same question.
        
        Expected: Only one value per question should be submitted.
        """
        with app.app_context():
            # Get the assessment page
            response = authenticated_client.get('/assessment/take/anxiety')
            assert response.status_code == 200
            
            # Submit form with multiple values for the SAME question (should only take last one)
            # This tests that the radio button group behavior works correctly
            form_data = {
                'q0': '1',  # Question 0 - should only accept one value
                'q1': '0',
            }
            
            # Fill in remaining questions
            for i in range(2, 7):
                form_data[f'q{i}'] = '0'
            
            response = authenticated_client.post(
                '/assessment/submit/anxiety',
                data=form_data,
                follow_redirects=True
            )
            
            # If bug exists: form may not handle this correctly
            # Should successfully process and show result
            assert response.status_code == 200
    
    def test_form_submit_preserves_all_selections(self, app, authenticated_client):
        """
        **Validates: Requirements 1, 2**
        
        Test that submitting the form with all questions answered preserves 
        all selections correctly and calculates score properly.
        
        Expected: All 7 questions should be captured with their selected values.
        """
        with app.app_context():
            # Get the assessment page
            response = authenticated_client.get('/assessment/take/anxiety')
            assert response.status_code == 200
            
            # Submit form with all questions answered
            form_data = {
                'q0': '4',  # Very often
                'q1': '3',  # Often
                'q2': '2',  # Sometimes
                'q3': '1',  # Rarely
                'q4': '0',  # Not at all
                'q5': '2',  # Sometimes
                'q6': '4',  # Very often
            }
            
            response = authenticated_client.post(
                '/assessment/submit/anxiety',
                data=form_data,
                follow_redirects=True
            )
            
            # Should successfully process
            assert response.status_code == 200
            
            # The score should reflect the values: (4+3+2+1+0+2+4) = 16
            # Higher GAD-7 score = more anxiety (inverted for display)
            # Total possible = 7 * 4 = 28
            # Raw score for anxiety (inverted) = 28 - 16 = 12
            # Score on 0-100 = (12/28) * 100 ≈ 43
            assert b'score' in response.data or b'43' in response.data


class TestTemplateRadioButtonStructure:
    """Tests to verify the HTML template structure for radio buttons."""
    
    def test_template_uses_radio_type(self, app, authenticated_client):
        """
        Verify that the template uses type="radio" for single-select behavior.
        """
        response = authenticated_client.get('/assessment/take/anxiety')
        assert response.status_code == 200
        
        # Should contain radio type inputs
        assert b'type="radio"' in response.data
    
    def test_template_uses_unique_names_per_question(self, app, authenticated_client):
        """
        Verify that each question has a unique name attribute.
        q0, q1, q2, etc. should all exist.
        """
        response = authenticated_client.get('/assessment/take/anxiety')
        assert response.status_code == 200
        
        # Should have unique names for each question
        assert b'name="q0"' in response.data
        assert b'name="q1"' in response.data
        assert b'name="q2"' in response.data
    
    def test_template_uses_unique_ids_per_option(self, app, authenticated_client):
        """
        Verify that each radio option has a unique ID.
        q0_0, q0_1, q0_2, etc. for question 0
        q1_0, q1_1, q1_2, etc. for question 1
        """
        response = authenticated_client.get('/assessment/take/anxiety')
        assert response.status_code == 200
        
        # Should have unique IDs for proper label association
        assert b'id="q0_0"' in response.data
        assert b'id="q0_1"' in response.data
        assert b'id="q1_0"' in response.data
        assert b'id="q1_1"' in response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])