INSERT INTO applicants (full_name, email, program, gpa, status, keywords_text)
VALUES
('Ada Lovelace', 'ada@example.com', 'MSCS', 3.95, 'submitted', 'distributed systems, compilers'),
('Alan Turing', 'alan@example.com', 'MSCS', 3.80, 'review', 'machine learning, theory'),
('Grace Hopper', 'grace@example.com', 'MSDS', 3.70, 'submitted', 'databases, systems')
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  program = VALUES(program),
  gpa = VALUES(gpa),
  status = VALUES(status),
  keywords_text = VALUES(keywords_text);