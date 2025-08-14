Feature: Application routes
  Verify key HTTP endpoints behave as expected

  Background: the app is running
    Given the application is running

  Scenario: Homepage returns HTML
    When I access the homepage
    Then I should see a webpage displayed

  Scenario: Healthcheck returns OK
    When I access the healthcheck endpoint
    Then I should receive status 200 and body "OK"

  Scenario: Feed page renders
    When I access the feed page for a known feed
    Then I should receive status 200 and HTML content

  Scenario: Click events page returns HTML table
    When I access the click events page
    Then I should receive status 200 and an HTML table

  Scenario: Redirect/track endpoint redirects to target
    When I access a redirect URL for a feed and link
    Then the response should be a 302 redirect

  Scenario: Refresh endpoint redirects to index
    When I access the refresh endpoint for a feed
    Then the response should be a 302 redirect to the index
