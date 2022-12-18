create table survey(
    id integer primary key,
    created datetime,
    tg_user_id integer,
    tg_username varchar(255),
    raw_text text
);