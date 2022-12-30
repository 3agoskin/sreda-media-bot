create table command_start(
    id integer primary key,
    created datetime,
    tg_user_id integer,
    tg_username varchar(255),
    come_from text
);

create table survey_new_year_tree(
    id integer primary key,
    tg_user_id integer,
    witch_tree text,
    why_this_choise text,
    where_bought text,
    when_bought text,
    which_eco text,
    why_eco text
);

create table sharing(
   id integer primary key,
   tg_user_id integer,
   tg_user_unique_link text
);