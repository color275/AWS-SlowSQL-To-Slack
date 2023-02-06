# 1. 목적
RDS/Aurora의 Slow Query 을 탐지하여 slack 을 통해 알림을 받는다.

# 2. Architecture
- Aurora 에서 Slow Query Log 가 CloudWatch 로 로깅 된다.
- CloudWatch의 로깅 Trigger에 의해 Lambda 가 수행 된다.
- Lambda 가 로그를 파싱하여 Slack 에 전달된다.
![alt text](img/iShot_2023-02-04_22.10.30.png)

# 3. 주의 사항
일반적으로 RDS/Aurora에서 Slow Query 를 Enable 하는 과정에서 downtime이나 지연은 발생하지 않으나 운영 환경의 경우에는 영향도가 적은 배포 시간이나 traffic이 적은 시간에 진행하시길 바랍니다

<br><br>

# 4. Aurora 설정

## 1. RDS Slow Query Enable
Aurora의 Slow Query 를 활성화 합니다.
1. Aurora 의 cluster 를 클릭
2. Modify 선택 
![alt text](img/iShot_2023-02-04_20.33.07.png)

`Additional configuration`섹션의 `Log exports` 에서 `Slow query log`를 체크합니다. ( 운영 안전성을 위해 Error log 와 Audit log를 체크하여 사용하는 것이 좋습니다. ) 
그리고 가장 하단의 `Continue` 버튼을 클릭합니다.
![alt text](img/iShot_2023-02-04_20.37.10.png)


1. Slow query log 가 선택되어 있는 것을 확인하고
2. Modify Cluster 를 클릭합니다.
![alt text](img/iShot_2023-02-04_20.40.03.png)


Aurora의 Staus 가 modify -> configuring-log-exports -> Available 될 때까지 기다립니다.
![alt text](img/iShot_2023-02-04_20.41.32.png)
![alt text](img/iShot_2023-02-04_20.45.06.png)

Configuration 탭에서 Slow query 가 활성화 되었는지 확인합니다.
1. Aurora 클러스터를 클릭
2. Configuration 탭 클릭
3. Slow query 확인
![alt text](img/iShot_2023-02-04_20.46.31.png)

## 2. 파라메터 그룹 확인
파라메터 그룹을 통해 Slow Query 상세 설정을 합니다.
1. DB Cluster parameter group을 확인합니다. 캡처 처럼 default.% (default.aurora-mysql5.7) 로 되어 있을 경우 별도의 파라페터 그룹을 생성하여 교체해주어야 합니다.

```diff
+ 별도의 파라메터 그룹으로 이미 매핑이 되어 있다면 3. 파라메터 그룹 상세 설정 으로 이동합니다.
```

![alt text](img/iShot_2023-02-04_20.50.11.png)

default.% 사용하고 있으므로 새로운 parameter group을 생성합니다.
1. Parameter group 클릭
2. Create parameter group 클릭
![alt text](img/iShot_2023-02-04_20.53.49.png)

1. 사용하고 있는 default.aurora-mysql5.7 에서 default를 제외하고 `aurora-mysql5.7` 를 선택합니다.
2. DB Cluster Prameter Group을 선택합니다.
3. `test-mysql-5-7` 을 입력합니다.
4. 적절한 명을 입력합니다.
5. Create 을 클릭합니다.
![alt text](img/iShot_2023-02-04_20.56.07.png)


Aurora의 parameter group을 방금 생성한 group으로 변경합니다.
1. database 클릭
2. aurora 클러스터 클릭
3. Modify 클릭
![alt text](img/iShot_2023-02-04_20.59.17.png)

`Additional configuration` 섹션의 `Database options` 에서 방금 생성한 `test-mysql-5-7`을 선택합니다.<br>
하단의 `Continue`를 클릭합니다.
![alt text](img/iShot_2023-02-04_21.01.01.png)


1. `test-mysql-5-7`로 변경된 것을 확인
2. `Apply immediately` 를 선택
3. `Modify Cluster` 클릭
![alt text](img/iShot_2023-02-04_21.03.39.png)


1. Cluster parameter group을 변경 했으므로 각 인스턴스에 적용이 됩니다. 인스턴스 클릭
2. 변경 중임을 확인합니다. Applying -> In sync
![alt text](img/iShot_2023-02-04_21.15.12.png)
![alt text](img/iShot_2023-02-04_21.19.21.png)

## 3. 파라메터 그룹 상세 설정
cluster parameter group 의 파라메터를 변경합니다.
1. Parameter group 선택
2. `test-mysql-5-7` 를 클릭 ( 데이터베이스 클러스터에 연결되어 있는 클러스터 파라메터 선택)
![alt text](img/iShot_2023-02-04_21.22.39.png)

Edit Parameters 를 클릭한 후 아래 파라메터를 변경합니다.
- slow_query_log : 1
- general_log : 1
- long_query_time : 3 (3초 이상만 수집, 요구사항에 따라 변경)
- log_output : FILE <br>

모두 변경한 후 `Save changes` 을 클릭합니다.
![alt text](img/iShot_2023-02-04_21.23.54.png)
![alt text](img/iShot_2023-02-04_21.25.20.png)

3초 이상 SQL 을 실행하여 Slow Query 로깅이 되는지 확인합니다.
- 3초 이상 SQL 실행
![alt text](img/iShot_2023-02-04_21.30.57.png)
- LOG 찾으러...
![alt text](img/iShot_2023-02-04_21.32.54.png)
- 3초 이상 실행된 SQL 이력 확인
![alt text](img/iShot_2023-02-04_21.34.15.png)


## 4. Slow Query 발생 시 Slack 알림
Lambda 생성 합니다.
- Create Lambda
![alt text](img/iShot_2023-02-04_21.40.13.png)

1. Author from scratch 선택
2. Lambda 명 입력 ( SlowQueryToSlack )
3. python3.8 선택
![alt text](img/iShot_2023-02-04_21.41.45.png)

- lambda.py (상단 소스에서 확인 가능) 에 있는 코드를 복사/붙여넣기
![alt text](img/iShot_2023-02-04_21.44.32.png)

- slack HOOK URL(기존에 사용하고 있는 Slack에서 확인) 값을 넣어주기 위해 변수를 등록 ( HOOK_URL : xxxxxx )
![alt text](img/iShot_2023-02-04_21.46.01.png)
![alt text](img/iShot_2023-02-04_21.48.13.png)

- Slow Log가 CloudWatch에 저장될 때 trigger 되도록 설정
![alt text](img/iShot_2023-02-04_21.49.29.png)



1. cloudwatch 선택
2. 모니터링하려는 db instance 명으로 필터
3. 결과중 db instance명/slowquery 선택
4. Filter name 입력 (slowQuery)
5. Add 버튼 클릭
![alt text](img/iShot_2023-02-04_21.51.12.png)

- trigger가 등록된 것을 확인합니다.
![alt text](img/iShot_2023-02-04_21.53.27.png)

다시 3초 이상 SQL을 실행 시켜 slack 으로 알람이 오는 것을 확인

- SQL 실행
![alt text](img/iShot_2023-02-04_21.54.30.png)
- Slack을 통해 3초 이상 SQL의 상세 정보 수신 확인
![alt text](img/iShot_2023-02-04_21.55.01.png)
