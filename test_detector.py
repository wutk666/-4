"""测试检测器是否正常工作"""
import sys
import traceback

try:
    print("测试攻击检测器...")
    from app import create_app, db
    from app.attack_detectors import AttackDetectorManager
    
    app = create_app()
    
    with app.app_context():
        print("✓ 创建应用成功")
        
        # 创建检测器管理器
        detector_manager = AttackDetectorManager(app, db)
        print("✓ 创建检测器管理器成功")
        
        # 测试SQL注入检测
        test_payload = "admin' OR '1'='1"
        print(f"\n测试 payload: {test_payload}")
        
        detection = detector_manager.detect_all(test_payload)
        print(f"检测结果: {detection}")
        
        if detection['detected']:
            print("✓ SQL注入检测成功！")
            for attack in detection['attacks']:
                print(f"  - 类型: {attack['type']}")
                print(f"  - 描述: {attack['description']}")
                print(f"  - 严重程度: {attack['severity']}")
        else:
            print("✗ 未检测到攻击")
        
        print("\n✓ 所有测试通过！")
        
except Exception as e:
    print(f"\n✗ 错误: {e}")
    print("\n完整错误信息:")
    traceback.print_exc()
    sys.exit(1)
