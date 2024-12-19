from tools.tools import perplexity_node

def perplexity_node_wrapper(state):
    """Wrapper function to call perplexity_node """
    print("Starting perplexity node")
    result = perplexity_node(state)
    print("Completed perplexity node")
    return result