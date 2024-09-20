""""
YO MEMORY IDEAS FROM FROM THE COUCH!!!!!

Create an internal memory as a deep copy of the main memory during `generate_response`. The chains should have a runnable lamda with a passthrough
to add to this memory if you want to track intermediate steps.


Main thought here is that chains should have there memory hidden from the main chat context


# BUG!!!!
Just realized that the Agents are recieving the query as both a query and in the history.

# LEFT OFF
just added fetch_memory start using this now!!! Goal here is to clean up the prompt that gets created for the RoleAgent.

I want clean memory, query 
"""