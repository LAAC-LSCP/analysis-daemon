"""
The domain module defines, in a domain-driven sense, the domain layer that contains the
definitions of our main entities, value objects, and aggregates.

Entities:
Tasks - tasks themselves, as defined according to our service needs (note that this is
    not necessarily the same as tasks are defined over the network/shared definition)

Value objects:
Commands - commands to be run on tasks, such as running or completing a task
Events - events to track what has happened, useful for logging

In our case there are no invariants to really worry about, except should they happen,
say scripts targeting the same files, we can include them as part of aggregates.
"""
