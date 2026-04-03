function onChange(e) {
  if (!e || (e.changeType !== 'INSERT_ROW' && e.changeType !== 'EDIT')) {
    return;
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();

  const row = sheet.getRange(lastRow, 1, 1, 7).getValues()[0];

  const ID_COL = 1;
  const TO_COL = 2;
  const SUBJECT_COL = 3;
  const BODY_COL = 4;
  const STATUS_COL = 5;
  const QUEUED_AT_COL = 6;
  const PROCESSED_AT_COL = 7;

  const id = row[ID_COL - 1];
  const to = row[TO_COL - 1];
  const subject = row[SUBJECT_COL - 1];
  const body = row[BODY_COL - 1];
  const status = row[STATUS_COL - 1];

  if (status !== 'PENDING') {
    return;
  }

  try {
    MailApp.sendEmail({
      to: to,
      subject: subject,
      body: body
    });

    sheet.getRange(lastRow, STATUS_COL).setValue('COMPLETED');
    sheet.getRange(lastRow, PROCESSED_AT_COL).setValue(formatDateTime());

  } catch (error) {
    sheet.getRange(lastRow, STATUS_COL).setValue('FAILED');
    sheet.getRange(lastRow, PROCESSED_AT_COL).setValue(formatDateTime());
  }
}

function formatDateTime() {
  const now = new Date();

  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');

  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');

  const millis = String(now.getMilliseconds()).padStart(3, '0');

  const micros = millis + "000";
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${micros}`;
}