var gulp = require('gulp'),
	minifyCss = require('gulp-minify-css'),
	minifyHtml = require('gulp-minify-html'),
	uglify = require('gulp-uglify'),
	usemin = require('gulp-usemin'),
	del = require('del');

var dir = {
	dev: '../src/',
	prod: '../dist/',
	vendor: './node_modules/'
};

/**
 * Main execution
 */
gulp.task('default', ['clean'], function() {
	gulp.start('index', '2018', 'images', 'data');
});

/**
 * index
 * A multi-task - parses HTML docs and applies supplied functions to any defined JS/CSS blocks
 */
gulp.task('index', function() {
	return gulp.src(dir.dev + 'index.html')
		.pipe(usemin({
			css: [minifyCss(), 'concat'],
			js_vendor: [uglify()],
			js_app: [uglify()],
			html: [minifyHtml({
				conditionals: true
			})]
		}))
		.pipe(gulp.dest(dir.prod));
});

/**
 * 2018
 * A multi-task - parses HTML docs and applies supplied functions to any defined JS/CSS blocks
 */
gulp.task('2018', function() {
	return gulp.src(dir.dev + '2018.html')
		.pipe(usemin({
			css: [minifyCss(), 'concat'],
			js_vendor: [uglify()],
			js_app: [uglify()],
			html: [minifyHtml({
				conditionals: true
			})]
		}))
		.pipe(gulp.dest(dir.prod));
});

/**
 * Images
 * Copies images directory to production folder
 */
gulp.task("images", function() {
    return gulp.src(dir.dev + "assets/images/**/*")
        .pipe(gulp.dest(dir.prod + "assets/images"));
});

/**
 * Data
 * Copies data directory to production folder
 */
gulp.task("data", function() {
    return gulp.src(dir.dev + "data/**/*")
        .pipe(gulp.dest(dir.prod + "data"));
});

/**
 * Clean
 * Cleans out the prod/build directory for a new compile
 */
gulp.task('clean', function(cb) {
	return del(dir.prod, {force: true}, cb);
});
