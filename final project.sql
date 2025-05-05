create database finalproject;
use finalproject;
create table borrower
(
borrowerid varchar(100) primary key,
age int,
income bigint,
newtocredit varchar(10),
gender varchar(10)
);
select * from borrower;

create table lender
(
lenderid int primary key,
lendername varchar(50)
);
select * from lender;

create table loantype
(
loantypeid int primary key,
typeofloan varchar(50)
);
select * from loantype;

create table loan
(
loanid varchar(100) primary key,
borrowid varchar(100) references borrower(borrowerid),
lenderid int references lender(lenderid),
loantypeid int references loantype(lontypeid),
originalloan bigint,
segmantofloan varchar(50),
quater varchar(10),
loanyear varchar(10)
);
select * from loan;

create table payment
(
paymentid varchar(50) primary key,
loanid varchar(50) references loan(loanid),
loantypeid int references loantype(lontypeid),
paymentamount bigint,
outstandingamount bigint
);
select * from payment;

ALTER TABLE loan
CHANGE COLUMN `ï»¿Loan Id` loanid varchar(50);

ALTER TABLE lender MODIFY lenderid INT AUTO_INCREMENT;
ALTER TABLE loan MODIFY `loanid` varchar(100) AUTO_INCREMENT;
ALTER TABLE loantype MODIFY loantypeid INT AUTO_INCREMENT;
ALTER TABLE borrower MODIFY borrowerid varchar(100) AUTO_INCREMENT;