# Feature: Storage Layer

## Problem

- The app will need to interface with the database to store Recipes, Ingredients, WeeklyPlans, ShoppingItems.
- The storage layer will be the interface to these SQLite tables.

## User Stories

- As an engineer/agent, I want to be able to CRUD on the models in `models/domain.py`.

## Constraints

- Follow the current models in `models/domain/py`.
- Stick with simple CRUD operations for each of models.
- Create an interface for each of the operations.

## Out of Scope

- Interfaces to get random Recipes.
