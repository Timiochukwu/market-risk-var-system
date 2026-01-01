# Day 037: Real-time Streaming Data with Kafka

**Duration**: 2 hours | **Difficulty**: Advanced | **Prerequisites**: Day 001-036

---

## 📋 What You'll Build

- Apache Kafka setup
- Real-time price streaming
- Stream processing with Kafka Streams
- Live VaR calculation
- Time-windowed aggregations
- Event-driven architecture

---

## 💻 Quick Implementation

```python
from kafka import KafkaProducer, KafkaConsumer
import json

# Producer - Stream market data
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send price update
producer.send('market-prices', {
    'ticker': 'AAPL',
    'price': 175.23,
    'timestamp': datetime.now().isoformat()
})

# Consumer - Calculate VaR in real-time
consumer = KafkaConsumer(
    'market-prices',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    price_data = message.value
    # Calculate VaR on streaming data
    var_amount = calculate_streaming_var(price_data)
    print(f"Real-time VaR: ${var_amount:,.2f}")
```

---

## ✅ Key Features

✅ Apache Kafka integration
✅ Real-time price streaming
✅ Stream processing
✅ Live VaR updates
✅ Event-driven architecture

**Next**: Microservices Architecture (Day 038)
