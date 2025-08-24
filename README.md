# Custom Message Samples

A comprehensive collection of custom message templates and samples for various use cases including customer service, marketing, notifications, error handling, and more.

## 📁 Files Overview

- **`custom_message_samples.txt`** - Human-readable text format with categorized message samples
- **`custom_message_samples.json`** - Structured JSON format for programmatic use
- **`message_samples_demo.py`** - Python demonstration script showing how to use the samples
- **`message_samples_template.html`** - Interactive web template for exploring and using message samples

## 🎯 Use Cases

### Customer Service
- Support responses
- Apology messages
- Escalation notifications
- Feedback acknowledgments

### Marketing
- Promotional offers
- Sales announcements
- Feature launches
- Limited-time deals

### System Messages
- Notifications
- Error messages
- Success confirmations
- Warning alerts
- Informational tips

### Business Communication
- Professional announcements
- Corporate updates
- Partnership communications
- Industry insights

### Specialized Messages
- Multilingual greetings
- Accessibility announcements
- Seasonal/holiday messages
- Emergency alerts
- Technical support responses

## 🚀 Getting Started

### 1. View Message Samples
Open `custom_message_samples.txt` to browse all available message templates in a readable format.

### 2. Use in Python Applications
```python
from message_samples_demo import MessageSampleManager

# Initialize manager
manager = MessageSampleManager()

# Get random message from specific category
message = manager.get_random_message("customer_service")

# Search for messages containing keywords
results = manager.search_messages("thank")

# Get all messages in a category
all_marketing = manager.get_all_messages_in_category("marketing")
```

### 3. Interactive Web Interface
Open `message_samples_template.html` in a web browser to:
- Browse messages by category
- Get random messages
- Search through all samples
- View message statistics

### 4. JSON Integration
Load `custom_message_samples.json` into your applications:
```python
import json

with open('custom_message_samples.json', 'r') as f:
    samples = json.load(f)

# Access specific category
customer_service_messages = samples['message_samples']['customer_service']
```

## 📊 Message Categories

| Category | Count | Description |
|----------|-------|-------------|
| Customer Service | 4 | Support and service-related messages |
| Marketing | 4 | Promotional and sales messages |
| Notifications | 4 | System and user notifications |
| Error Messages | 4 | Error handling and user guidance |
| Success Messages | 4 | Confirmation and completion messages |
| Warnings | 4 | Cautionary and alert messages |
| Informational | 4 | Tips, facts, and helpful information |
| Social Media | 4 | Social media style communications |
| Professional Business | 4 | Corporate and business communications |
| Emergency/Urgent | 4 | Critical and time-sensitive alerts |
| Multilingual | 4 | Multi-language message examples |
| Accessibility | 4 | Accessibility-focused communications |
| Seasonal/Holiday | 4 | Time-based and celebratory messages |
| Technical Support | 4 | Technical assistance and guidance |
| Feedback Collection | 4 | User feedback and survey messages |

**Total: 16 categories, 64 messages**

## 🛠️ Customization

### Adding New Messages
1. **Text Format**: Add new messages to `custom_message_samples.txt`
2. **JSON Format**: Update `custom_message_samples.json` with new entries
3. **Python Script**: Modify the `_get_default_samples()` method in the demo script

### Adding New Categories
1. Create a new section in the text file
2. Add the category to the JSON structure
3. Update the HTML template dropdown options
4. Modify the Python demo script accordingly

## 🔍 Search and Filtering

### Keyword Search
Search through all messages using specific keywords:
- Customer service terms: "thank", "apologize", "support"
- Technical terms: "error", "warning", "system"
- Business terms: "announcement", "partnership", "update"

### Category Filtering
Browse messages by specific categories to find relevant templates for your use case.

## 📱 Responsive Design

The HTML template is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile devices
- Various screen sizes

## 🎨 Styling and Themes

The web template features:
- Modern gradient design
- Clean, professional appearance
- Consistent color scheme
- Smooth hover effects
- Card-based layout

## 🤝 Contributing

To add new message samples or improve existing ones:

1. **Fork the repository**
2. **Add your messages** to the appropriate files
3. **Test the changes** using the demo script
4. **Submit a pull request** with your improvements

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

If you need help or have questions about using these message samples:

1. Check the demo script for usage examples
2. Review the HTML template for web integration
3. Examine the JSON structure for API integration
4. Open an issue for specific problems or feature requests

## 🔄 Updates

The message samples are regularly updated with:
- New categories based on user needs
- Improved message templates
- Additional language support
- Enhanced accessibility features

---

**Happy messaging! 🚀**
