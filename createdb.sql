create table command_start(
    id integer primary key,
    created datetime,
    tg_user_id integer,
    come_from text
);

create table survey_new_year_tree_total(
    id integer primary key,
    created datetime,
    tg_user_id integer,
    liked boolean,
    share text,
    reason_dislike text
);
