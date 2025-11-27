from flask_mail import Message
from app import mail

def send_inquiry_answer_email(to_email, title, answer):
  """고객센터 문의 답변 이메일 발송"""
  msg = Message(
    subject=f"[문의답변] {title}",
    recipients=[to_email],
    charset="utf-8"
  )

  # 줄바꿈 → <br> 변환
  formatted_answer = answer.replace("\n", "<br>") if answer else ""

  # HTML 버전
  msg.html = f"""
  <div style="font-family: 'Noto Sans KR', Arial, sans-serif; padding: 26px; line-height: 1.6; font-size: 15px; color: #222;">
    
    <h2 style="margin-top: 0; font-size: 20px; font-weight: 700; color: #333;">
      고객센터 문의 답변 안내
    </h2>

    <p>안녕하세요, 고객님 😊<br>
    남겨주신 문의에 대한 답변을 아래와 같이 보내드립니다.</p>

    <div style="border-left: 4px solid #7a5cff; padding: 14px 18px; background: #faf7ff; margin: 18px 0; border-radius: 6px;">
      <p style="margin: 0; font-size: 14px; color: #555;">
        <strong style="font-size: 15px; color: #333;">📌 문의 제목</strong><br>
        {title}
      </p>
      <hr style="border: 0; border-top: 1px solid #ddd; margin: 14px 0;">
      <p style="margin: 0; font-size: 14px; color: #555;">
        <strong style="font-size: 15px; color: #333;">📝 답변 내용</strong><br>
        {formatted_answer}
      </p>
    </div>

    <p>추가로 궁금하신 점이 있으시다면 언제든지 고객센터로 문의해주세요.</p>

    <p style="margin-top: 38px; font-size: 13px; color:#777;">
      감사합니다.<br>
      <strong style="color:#7a5cff;">고객센터 드림</strong>
    </p>

  </div>
  """
  msg.body = (
    f"안녕하세요, 고객님.\n"
    f"문의하신 내용에 대한 답변입니다.\n\n"
    f"------------------------------------\n"
    f"문의 제목: {title}\n\n"
    f"관리자 답변:\n{answer}\n"
    f"------------------------------------\n\n"
    f"궁금하신 점이 있으면 언제든 다시 문의해주세요.\n"
    f"감사합니다."
  )

  mail.send(msg)

