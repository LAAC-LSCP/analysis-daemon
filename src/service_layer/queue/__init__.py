"""
The queue module defines two types of queues (command queues and event queues), which
track the commands and events. Both queues actually wrap asyncio queues, which actively
run the callbacks that need to be run
Queues in our code are responsible for handling this queue, and on their own are
designed with testability in mind by "ticking", with each tick deciding what to add to
the queue that is still waiting

The algorithm for events is simply to greedily handle them, as they are short-lived

The command queue acts as a priority queue, with priority calculated according to the
command data.

Both queues are contained by a single broker which can route a message to either queue,
for the moment simply depending on the type of message (a Command or an Event?)

TODO: Outline the command queue algorithm
"""
