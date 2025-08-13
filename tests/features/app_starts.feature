Feature: Application Startup
  As a user
  I want to verify the application starts and serves a webpage

  Scenario: Application starts and displays homepage
    Given the application is running
    When I access the homepage
    Then I should see a webpage displayed
