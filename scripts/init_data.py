"""
初始化食物和运动数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import SessionLocal, engine, Base
import models

# 创建所有表
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # 初始化食物数据
    foods_data = [
        {"name": "米饭", "category": "主食", "calories_per_100g": 116, "protein_per_100g": 2.6, "carbs_per_100g": 25.9},
        {"name": "馒头", "category": "主食", "calories_per_100g": 223, "protein_per_100g": 7.0, "carbs_per_100g": 47.0},
        {"name": "面条", "category": "主食", "calories_per_100g": 110, "protein_per_100g": 2.7, "carbs_per_100g": 24.3},
        {"name": "面包", "category": "主食", "calories_per_100g": 265, "protein_per_100g": 9.0, "carbs_per_100g": 49.0},
        {"name": "鸡蛋", "category": "蛋类", "calories_per_100g": 144, "protein_per_100g": 13.0, "fat_per_100g": 9.9},
        {"name": "鸡胸肉", "category": "肉类", "calories_per_100g": 118, "protein_per_100g": 24.6, "fat_per_100g": 1.2},
        {"name": "牛肉", "category": "肉类", "calories_per_100g": 250, "protein_per_100g": 20.0, "fat_per_100g": 18.0},
        {"name": "猪肉", "category": "肉类", "calories_per_100g": 395, "protein_per_100g": 13.0, "fat_per_100g": 37.0},
        {"name": "鱼肉", "category": "肉类", "calories_per_100g": 105, "protein_per_100g": 20.0, "fat_per_100g": 2.0},
        {"name": "牛奶", "category": "奶制品", "calories_per_100g": 54, "protein_per_100g": 3.0, "carbs_per_100g": 5.0},
        {"name": "酸奶", "category": "奶制品", "calories_per_100g": 72, "protein_per_100g": 3.0, "carbs_per_100g": 10.0},
        {"name": "苹果", "category": "水果", "calories_per_100g": 52, "protein_per_100g": 0.3, "carbs_per_100g": 14.0},
        {"name": "香蕉", "category": "水果", "calories_per_100g": 89, "protein_per_100g": 1.1, "carbs_per_100g": 23.0},
        {"name": "橙子", "category": "水果", "calories_per_100g": 47, "protein_per_100g": 0.9, "carbs_per_100g": 12.0},
        {"name": "葡萄", "category": "水果", "calories_per_100g": 67, "protein_per_100g": 0.6, "carbs_per_100g": 17.0},
        {"name": "西兰花", "category": "蔬菜", "calories_per_100g": 34, "protein_per_100g": 2.8, "carbs_per_100g": 7.0},
        {"name": "胡萝卜", "category": "蔬菜", "calories_per_100g": 41, "protein_per_100g": 0.9, "carbs_per_100g": 10.0},
        {"name": "西红柿", "category": "蔬菜", "calories_per_100g": 18, "protein_per_100g": 0.9, "carbs_per_100g": 3.9},
        {"name": "黄瓜", "category": "蔬菜", "calories_per_100g": 16, "protein_per_100g": 0.7, "carbs_per_100g": 3.6},
        {"name": "土豆", "category": "蔬菜", "calories_per_100g": 77, "protein_per_100g": 2.0, "carbs_per_100g": 17.0},
    ]
    
    for food_data in foods_data:
        existing = db.query(models.Food).filter(models.Food.name == food_data["name"]).first()
        if not existing:
            food = models.Food(**food_data)
            db.add(food)
    
    # 初始化运动数据
    sports_data = [
        {"name": "跑步", "category": "有氧运动", "calories_per_hour": 600, "intensity_level": "高强度"},
        {"name": "快走", "category": "有氧运动", "calories_per_hour": 300, "intensity_level": "低强度"},
        {"name": "游泳", "category": "有氧运动", "calories_per_hour": 500, "intensity_level": "高强度"},
        {"name": "骑自行车", "category": "有氧运动", "calories_per_hour": 400, "intensity_level": "中等强度"},
        {"name": "跳绳", "category": "有氧运动", "calories_per_hour": 700, "intensity_level": "高强度"},
        {"name": "瑜伽", "category": "室内运动", "calories_per_hour": 200, "intensity_level": "低强度"},
        {"name": "健身操", "category": "有氧运动", "calories_per_hour": 350, "intensity_level": "中等强度"},
        {"name": "篮球", "category": "球类运动", "calories_per_hour": 450, "intensity_level": "高强度"},
        {"name": "足球", "category": "球类运动", "calories_per_hour": 500, "intensity_level": "高强度"},
        {"name": "羽毛球", "category": "球类运动", "calories_per_hour": 400, "intensity_level": "中等强度"},
        {"name": "乒乓球", "category": "球类运动", "calories_per_hour": 350, "intensity_level": "中等强度"},
        {"name": "网球", "category": "球类运动", "calories_per_hour": 450, "intensity_level": "高强度"},
        {"name": "力量训练", "category": "力量训练", "calories_per_hour": 300, "intensity_level": "中等强度"},
        {"name": "哑铃训练", "category": "力量训练", "calories_per_hour": 350, "intensity_level": "中等强度"},
        {"name": "引体向上", "category": "力量训练", "calories_per_hour": 400, "intensity_level": "高强度"},
        {"name": "俯卧撑", "category": "力量训练", "calories_per_hour": 350, "intensity_level": "中等强度"},
        {"name": "登山", "category": "户外运动", "calories_per_hour": 450, "intensity_level": "高强度"},
        {"name": "徒步", "category": "户外运动", "calories_per_hour": 350, "intensity_level": "中等强度"},
    ]
    
    for sport_data in sports_data:
        existing = db.query(models.Sport).filter(models.Sport.name == sport_data["name"]).first()
        if not existing:
            sport = models.Sport(**sport_data)
            db.add(sport)
    
    db.commit()
    print("初始化数据完成！")
    print(f"添加了 {len(foods_data)} 种食物")
    print(f"添加了 {len(sports_data)} 种运动")
    
except Exception as e:
    db.rollback()
    print(f"初始化失败：{e}")
finally:
    db.close()
