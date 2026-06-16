import os
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_alibaba import ChatBailian

# === 1. Domain tools: SmartMart e-commerce support ===

@tool
def order_lookup(order_id: str = "", customer_email: str = "") -> dict:
    """Look up order details and status by order ID (SM-XXXXXXXX) or customer email."""
    if order_id:
        return order_service.get_by_id(order_id)
    elif customer_email:
        return order_service.get_by_email(customer_email)
    return {"error": "Please provide order_id or customer_email"}

@tool
def product_search(query: str, category: str = "", brand: str = "",
                   min_price: float = 0, max_price: float = 99999,
                   in_stock_only: bool = True) -> dict:
    """Search product catalog by keywords, category, brand, or price range."""
    return catalog_service.search(
        query=query, category=category, brand=brand,
        min_price=min_price, max_price=max_price,
        in_stock_only=in_stock_only
    )

@tool
def initiate_return(order_id: str, item_id: str, reason: str, resolution: str) -> dict:
    """Start return/refund process. Reason: defective|wrong_item|doesnt_fit|not_as_described|changed_mind|arrived_damaged. Resolution: refund|exchange|store_credit."""
    return after_sales.create_return(
        order_id=order_id, item_id=item_id,
        reason=reason, resolution=resolution
    )

@tool
def track_shipment(tracking_number: str = "", order_id: str = "") -> dict:
    """Get real-time shipment tracking by tracking number or order ID."""
    if tracking_number:
        return logistics_api.track(tracking_number)
    elif order_id:
        return logistics_api.track_by_order(order_id)
    return {"error": "Please provide tracking_number or order_id"}

@tool
def escalate_to_human(reason: str, priority: str = "medium",
                      conversation_summary: str = "") -> dict:
    """Transfer conversation to live human agent. Priority: low|medium|high|urgent."""
    return escalation_service.transfer(
        reason=reason, priority=priority,
        summary=conversation_summary
    )

@tool
def check_promotion(promo_code: str = "", category: str = "") -> dict:
    """Validate a promo code or look up active promotions for a category."""
    if promo_code:
        return promo_service.validate(promo_code)
    elif category:
        return promo_service.get_active(category)
    return promo_service.get_all_active()

# === 2. Bind to Bailian via the AI Gateway ===
llm = ChatBailian(
    model="qwen-max",
    base_url="https://higress.agentrun.internal/v1",  # AI Gateway
    api_key=os.getenv("BAILIAN_KEY"),
    temperature=0.3,
    max_tokens=1024,
)

# === 3. System prompt: SmartMart Smart Assistant ===
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are Smart Assistant, the AI-powered customer support agent for "
     "SmartMart — a general marketplace operating across Southeast Asia, "
     "East Asia, and Oceania.\n\n"
     "ROLE: Help customers with product inquiries, order tracking, returns & "
     "refunds, shipping questions, payment issues, and account support.\n\n"
     "GUIDELINES:\n"
     "- Be warm, professional, and solution-oriented. Keep responses under 150 words.\n"
     "- Only provide information from the SmartMart knowledge base.\n"
     "- If you cannot resolve after 2 attempts, or customer requests it, escalate to human.\n"
     "- Never ask for full credit card numbers, passwords, or national IDs.\n"
     "- After resolving, offer one relevant follow-up suggestion.\n"
     "- End with: 'Is there anything else I can help you with?'\n\n"
     "SCOPE: SmartMart-related queries only. Politely decline off-topic requests.\n\n"
     "TOOLS: order_lookup, product_search, initiate_return, track_shipment, "
     "escalate_to_human, check_promotion"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# === 4. Create agent and executor ===
tools = [order_lookup, product_search, initiate_return,
         track_shipment, escalate_to_human, check_promotion]

agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,
)

# === 5. AgentRun HTTP handler — endpoint provisioned on deploy ===
def handler(event):
    """Entry point for FC AgentRun. Receives customer query, returns agent response."""
    user_input = event.get("query", "")
    chat_history = event.get("chat_history", [])

    result = executor.invoke({
        "input": user_input,
        "chat_history": chat_history,
    })

    return {
        "response": result["output"],
        "agent": "Smart Assistant",
        "version": "1.0.0",
    }
