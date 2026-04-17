import { NextResponse } from "next/server";
import { z } from "zod";

const schema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  subject: z.string().min(3),
  message: z.string().min(20),
  privacy: z.literal(true),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const data = schema.parse(body);

    // When RESEND_API_KEY is set, send via Resend. Otherwise log locally.
    const resendKey = process.env.RESEND_API_KEY;

    if (resendKey) {
      const res = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${resendKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: "Kontaktformular <noreply@reichenberg.ruhr>",
          to: ["info@reichenberg.ruhr"],
          reply_to: data.email,
          subject: `Neue Anfrage: ${data.subject} – ${data.name}`,
          html: `
            <h2>Neue Kontaktanfrage</h2>
            <p><strong>Name:</strong> ${data.name}</p>
            <p><strong>E-Mail:</strong> ${data.email}</p>
            <p><strong>Thema:</strong> ${data.subject}</p>
            <p><strong>Nachricht:</strong></p>
            <p>${data.message.replace(/\n/g, "<br>")}</p>
          `,
        }),
      });

      if (!res.ok) {
        return NextResponse.json({ error: "Email send failed" }, { status: 500 });
      }
    } else {
      console.log("[Contact Form]", data);
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: "Validation failed", details: err.errors }, { status: 400 });
    }
    return NextResponse.json({ error: "Internal error" }, { status: 500 });
  }
}
