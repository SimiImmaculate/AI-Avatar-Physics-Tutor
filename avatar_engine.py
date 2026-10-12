# =========================================================
# PHYSICS MENTOR AVATAR
# =========================================================

AVATAR_STATES = {

    "idle": {
        "emoji": "👨‍🏫",
        "title": "Physics Mentor",
        "message": "Ask me anything about Physics!"
    },

    "listening": {
        "emoji": "🎤",
        "title": "Listening...",
        "message": "I'm listening to your Physics question."
    },

    "thinking": {
        "emoji": "🧠",
        "title": "Thinking...",
        "message": "Let me work through this carefully."
    },

    "speaking": {
        "emoji": "🔊",
        "title": "Explaining...",
        "message": "Here is your step-by-step explanation."
    },

    "quiz": {
        "emoji": "🎯",
        "title": "Quiz Mode",
        "message": "Let's test your Physics understanding!"
    },

    "success": {
        "emoji": "🎉",
        "title": "Excellent!",
        "message": "Great work! Keep building your Physics skills."
    }
}


def get_avatar_state(state):

    return AVATAR_STATES.get(
        state,
        AVATAR_STATES["idle"]
    )