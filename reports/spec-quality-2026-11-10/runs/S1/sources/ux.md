선택 객체는 현재 필터 목록과 별도로 유지합니다. loading/성공 empty/요청 error를 서로 구분합니다. loading과 error에서도 선택 패널을 비우지 않습니다. Retry는 현재 상태 필터를 사용합니다. 오래된 성공·실패·finally 처리로 새 필터 결과가 바뀌지 않게 합니다.
