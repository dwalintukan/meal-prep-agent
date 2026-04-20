# Feature: Database Connection

## Problem
The app will need to insert and read Recipes for weekly meal planning.
It will also need to read the previous WeeklyPlan to ensure we don't get the same recipes.
These all require a database connection to the SQLite DB.

## User Stories
- As an engineer/agent, I need to have the database connection set up to interface with the DB.
- As an engineer, I want to ensure we only have a single DB connection across the whole app.

## Out of Scope
- Database schemas
- ORM integration

## Constraints
- Must use aiosqlite (already a project dependency)
- Must have a singular database connection for the entire app
- Any files should be able to import this singular database connection
